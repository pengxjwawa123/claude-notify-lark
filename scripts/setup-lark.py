#!/usr/bin/env python3
"""claude-lark Lark-only 一键安装器（交互式）。

零依赖，仅用标准库。流程：收集凭据 → 取 token → 查 open_id
（手机号查不到自动提示改用邮箱）→ 写 config → 注册 hook → 发测试消息。

仅支持 Lark 国际版（open.larksuite.com）。
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

# ── 固定 Lark 国际版域名 ──────────────────────────────────────────────
BASE = "https://open.larksuite.com/open-apis"
TOKEN_URL = f"{BASE}/auth/v3/tenant_access_token/internal/"
LOOKUP_URL = f"{BASE}/contact/v3/users/batch_get_id?user_id_type=open_id"
MESSAGE_URL = f"{BASE}/im/v1/messages?receive_id_type=open_id"

CONFIG_DIR = Path.home() / ".config" / "claude-lark"
CONFIG_PATH = CONFIG_DIR / "config.json"
NOTIFY_PATH = Path.home() / ".claude-lark" / "claude_lark_notify.py"


def _api_post(url: str, payload: dict, token: str | None = None) -> dict:
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read())
        except (json.JSONDecodeError, ValueError):
            return {"code": -1, "msg": f"HTTP {e.code}"}
    except (urllib.error.URLError, OSError) as e:
        return {"code": -1, "msg": str(e)}


def get_token(app_id: str, app_secret: str) -> str:
    resp = _api_post(TOKEN_URL, {"app_id": app_id, "app_secret": app_secret})
    if resp.get("code") != 0:
        raise RuntimeError(
            f"获取 token 失败：code={resp.get('code')} msg={resp.get('msg')}\n"
            f"请检查 App ID / App Secret 是否正确（应为 Lark 国际版应用）。"
        )
    return resp["tenant_access_token"]


def resolve_open_id(token: str, kind: str, value: str) -> str | None:
    """kind 为 'phone' 或 'email'。查到返回 open_id；查不到返回 None。"""
    payload = {"mobiles": [value]} if kind == "phone" else {"emails": [value]}
    resp = _api_post(LOOKUP_URL, payload, token)
    if resp.get("code") != 0:
        raise RuntimeError(
            f"查询 open_id 失败：code={resp.get('code')} msg={resp.get('msg')}\n"
            f"若为 99991672，请到 Lark 后台开通 contact:user.id:readonly 权限并发版。"
        )
    users = resp.get("data", {}).get("user_list", [])
    if users and users[0].get("user_id"):
        return users[0]["user_id"]
    return None


def write_config(app_id: str, app_secret: str, open_id: str) -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cfg = {
        "app_id": app_id,
        "app_secret": app_secret,
        "open_id": open_id,
        "events": ["Stop", "Notification"],
    }
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=4)
    try:
        CONFIG_PATH.chmod(0o600)
    except (OSError, AttributeError):
        pass
    return CONFIG_PATH


def send_test(token: str, open_id: str) -> bool:
    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "✅ claude-lark 配置成功"},
            "template": "green",
        },
        "elements": [
            {"tag": "markdown",
             "content": "你已成功配置 claude-lark 通知！\n\n从现在起，Claude Code 完成任务或需要确认时，你都会收到 Lark 通知。"},
        ],
    }
    resp = _api_post(MESSAGE_URL, {
        "receive_id": open_id, "msg_type": "interactive",
        "content": json.dumps(card, ensure_ascii=False),
    }, token)
    if resp.get("code") == 0:
        return True
    print(f"WARN: 测试消息发送失败：code={resp.get('code')} msg={resp.get('msg')}")
    return False


import os
import shutil


def _settings_path() -> Path:
    base = os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")
    return Path(base) / "settings.json"


def register_hook() -> bool:
    """幂等注册 Stop/Notification hook，写前备份，不动其他 hook。
    返回是否发生改动。"""
    sp = _settings_path()
    cmd = f"python3 {NOTIFY_PATH}"

    if sp.exists():
        try:
            settings = json.loads(sp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            raise RuntimeError(f"settings.json 不是合法 JSON，请手动检查：{sp}")
        shutil.copy2(sp, sp.with_suffix(".json.bak"))
    else:
        sp.parent.mkdir(parents=True, exist_ok=True)
        settings = {}

    hooks = settings.setdefault("hooks", {})
    changed = False
    for event in ("Stop", "Notification"):
        groups = hooks.setdefault(event, [])
        already = any(
            h.get("command") == cmd
            for g in groups
            for h in g.get("hooks", [])
        )
        if not already:
            groups.append({
                "matcher": "",
                "hooks": [{"type": "command", "command": cmd, "timeout": 30}],
            })
            changed = True

    if changed:
        sp.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    return changed


def _prompt(label: str) -> str:
    val = input(label).strip()
    while not val:
        val = input(label).strip()
    return val


def main() -> int:
    print("claude-lark 安装器（Lark 国际版）\n" + "─" * 36)
    app_id = _prompt("App ID (cli_...): ")
    app_secret = _prompt("App Secret: ")

    try:
        token = get_token(app_id, app_secret)
        print("✓ token 获取成功")
    except RuntimeError as e:
        print(f"✗ {e}")
        return 1

    open_id = None
    choice = _prompt("用 [1] 手机号 还是 [2] 邮箱 查询 open_id? (1/2): ")
    kind = "phone" if choice == "1" else "email"
    value = _prompt("请输入手机号: " if kind == "phone" else "请输入邮箱: ")

    try:
        open_id = resolve_open_id(token, kind, value)
    except RuntimeError as e:
        print(f"✗ {e}")
        return 1

    if not open_id and kind == "phone":
        print("! 该手机号在组织内未匹配，请改用邮箱。")
        email = _prompt("请输入邮箱: ")
        try:
            open_id = resolve_open_id(token, "email", email)
        except RuntimeError as e:
            print(f"✗ {e}")
            return 1

    if not open_id:
        print("✗ 未能查到 open_id，请确认该用户在应用可用范围内。")
        return 1
    print(f"✓ open_id: {open_id}")

    path = write_config(app_id, app_secret, open_id)
    print(f"✓ 配置已写入 {path}")

    try:
        changed = register_hook()
        print("✓ hook 已注册" if changed else "✓ hook 已存在，跳过")
    except RuntimeError as e:
        print(f"✗ {e}")
        return 1

    if send_test(token, open_id):
        print("✓ 测试消息已发送，请到 Lark 查收")
    print("\n完成！")
    return 0


if __name__ == "__main__":
    sys.exit(main())
