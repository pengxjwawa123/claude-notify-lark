# claude-lark Lark-only 私有化封装 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `~/.claude-lark` 项目封装成 pengxjwawa 自己的、只支持 Lark 国际版的项目，新增一键安装脚本 `setup-lark.py`，用干净的初始提交推送到 `github.com/pengxjwawa/claude-lark`。

**Architecture:** 在现有项目原地改造：① 把所有 API 域名从 `open.feishu.cn` 固定为 `open.larksuite.com`（含项目根脚本与 `.claude/plugins/claude-lark/` 插件镜像副本两套）；② 新增独立的 `scripts/setup-lark.py` 交互式安装器；③ 把上游 `ysyecust` 标识全部替换为 `pengxjwawa`、删除英文 README；④ 清除 git 历史重新初始化并推送。

**Tech Stack:** Python 3 标准库（urllib/json/argparse/pathlib）、Bash、Git、Claude Code 插件清单（JSON）。

---

## 文件结构

**新建：**
- `scripts/setup-lark.py` — Lark-only 交互式一键安装器（核心新增）

**修改（域名 feishu → larksuite）：**
- `claude_lark_notify.py`（已手动改过，确认即可）
- `scripts/setup.py`
- `scripts/install.sh`
- `scripts/install.ps1`
- `scripts/admin-setup.sh`
- `.claude/plugins/claude-lark/claude_lark_notify.py`（插件镜像副本）
- `.claude/plugins/claude-lark/scripts/setup.py`（插件镜像副本）

**修改（去上游痕迹 ysyecust → pengxjwawa）：**
- `.claude-plugin/marketplace.json`
- `.claude/plugins/claude-lark/.claude-plugin/plugin.json`
- `scripts/install-remote.sh`
- `README.md`
- `CONTRIBUTING.md`

**修改（插件命令对齐新脚本）：**
- `.claude/plugins/claude-lark/skills/setup-lark.md`

**删除：**
- `README_en.md`

---

## Task 1: 确认 notify 脚本域名修复已落地

**Files:**
- Verify: `claude_lark_notify.py:49-51`
- Modify: `.claude/plugins/claude-lark/claude_lark_notify.py`

- [ ] **Step 1: 检查根脚本域名**

Run: `grep -n "larksuite\|feishu" /Users/mac/.claude-lark/claude_lark_notify.py`
Expected: 第 49、51 行显示 `open.larksuite.com`，无 `feishu` 残留。（已在之前修复，确认即可。）

- [ ] **Step 2: 改插件镜像副本的域名**

把 `.claude/plugins/claude-lark/claude_lark_notify.py` 中的两处域名改为 larksuite：

将
```python
LARK_TOKEN_URL = (
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"
)
LARK_MESSAGE_URL = "https://open.feishu.cn/open-apis/im/v1/messages"
```
改为
```python
LARK_TOKEN_URL = (
    "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal/"
)
LARK_MESSAGE_URL = "https://open.larksuite.com/open-apis/im/v1/messages"
```

- [ ] **Step 3: 验证两套 notify 脚本均无 feishu 残留**

Run: `grep -rn "feishu.cn" /Users/mac/.claude-lark/claude_lark_notify.py /Users/mac/.claude-lark/.claude/plugins/claude-lark/claude_lark_notify.py`
Expected: 无输出（exit 1）。

- [ ] **Step 4: 提交**

```bash
cd /Users/mac/.claude-lark
git add claude_lark_notify.py .claude/plugins/claude-lark/claude_lark_notify.py
git commit -m "fix: pin notify domain to larksuite (intl Lark)"
```

---

## Task 2: 编写 setup-lark.py — 基础骨架与 API 函数

**Files:**
- Create: `scripts/setup-lark.py`

- [ ] **Step 1: 写文件头与 API 辅助函数**

创建 `/Users/mac/.claude-lark/scripts/setup-lark.py`，写入：

```python
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
```

- [ ] **Step 2: 语法检查**

Run: `python3 -m py_compile /Users/mac/.claude-lark/scripts/setup-lark.py && echo OK`
Expected: `OK`

- [ ] **Step 3: 提交**

```bash
cd /Users/mac/.claude-lark
git add scripts/setup-lark.py
git commit -m "feat: setup-lark.py skeleton with Lark API helpers"
```

---

## Task 3: setup-lark.py — token 与 open_id 解析（含手机号→邮箱回退）

**Files:**
- Modify: `scripts/setup-lark.py`

- [ ] **Step 1: 追加 get_token 与 resolve_open_id 函数**

在 `_api_post` 之后追加：

```python
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
```

- [ ] **Step 2: 语法检查**

Run: `python3 -m py_compile /Users/mac/.claude-lark/scripts/setup-lark.py && echo OK`
Expected: `OK`

- [ ] **Step 3: 用真实凭据冒烟测试 token + 邮箱查询**

Run:
```bash
cd /Users/mac/.claude-lark && python3 -c "
import sys; sys.path.insert(0,'scripts')
import importlib.util
spec=importlib.util.spec_from_file_location('s','scripts/setup-lark.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
import json
cfg=json.load(open('$HOME/.config/claude-lark/config.json'.replace('\$HOME','$HOME')))
t=m.get_token(cfg['app_id'], cfg['app_secret'])
print('token ok:', bool(t))
oid=m.resolve_open_id(t,'email','pengxjwawa@gmail.com')
print('email open_id:', oid)
print('phone open_id:', m.resolve_open_id(t,'phone','18290335368'))
"
```
Expected: `token ok: True`、`email open_id: ou_3a1d68eb16f4d3787de58bfdc378cc6d`、`phone open_id: None`（验证手机号回退路径）。

- [ ] **Step 4: 提交**

```bash
cd /Users/mac/.claude-lark
git add scripts/setup-lark.py
git commit -m "feat: token and open_id resolution with phone-to-email fallback"
```

---

## Task 4: setup-lark.py — 写 config 与发测试消息

**Files:**
- Modify: `scripts/setup-lark.py`

- [ ] **Step 1: 追加 write_config 与 send_test 函数**

在 `resolve_open_id` 之后追加：

```python
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
```

- [ ] **Step 2: 语法检查**

Run: `python3 -m py_compile /Users/mac/.claude-lark/scripts/setup-lark.py && echo OK`
Expected: `OK`

- [ ] **Step 3: 提交**

```bash
cd /Users/mac/.claude-lark
git add scripts/setup-lark.py
git commit -m "feat: write_config and send_test for setup-lark"
```

---

## Task 5: setup-lark.py — 幂等注册 hook

**Files:**
- Modify: `scripts/setup-lark.py`

- [ ] **Step 1: 追加 register_hook 函数**

在 `send_test` 之后追加：

```python
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
```

- [ ] **Step 2: 语法检查**

Run: `python3 -m py_compile /Users/mac/.claude-lark/scripts/setup-lark.py && echo OK`
Expected: `OK`

- [ ] **Step 3: 幂等性单元验证（临时 settings 文件）**

Run:
```bash
cd /Users/mac/.claude-lark && CLAUDE_CONFIG_DIR=/tmp/cl_test python3 -c "
import importlib.util, json, os
spec=importlib.util.spec_from_file_location('s','scripts/setup-lark.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
os.makedirs('/tmp/cl_test', exist_ok=True)
# 预置一个已有的无关 hook
json.dump({'hooks':{'PreToolUse':[{'matcher':'Bash','hooks':[{'type':'command','command':'echo rtk'}]}]}}, open('/tmp/cl_test/settings.json','w'))
print('first run changed:', m.register_hook())
print('second run changed:', m.register_hook())
s=json.load(open('/tmp/cl_test/settings.json'))
print('Stop groups:', len(s['hooks']['Stop']))
print('rtk preserved:', s['hooks']['PreToolUse'][0]['hooks'][0]['command']=='echo rtk')
"
```
Expected: `first run changed: True`、`second run changed: False`、`Stop groups: 1`、`rtk preserved: True`。

- [ ] **Step 4: 清理临时文件**

Run: `rm -rf /tmp/cl_test && echo cleaned`
Expected: `cleaned`

- [ ] **Step 5: 提交**

```bash
cd /Users/mac/.claude-lark
git add scripts/setup-lark.py
git commit -m "feat: idempotent hook registration for setup-lark"
```

---

## Task 6: setup-lark.py — 交互式 main 串联

**Files:**
- Modify: `scripts/setup-lark.py`

- [ ] **Step 1: 追加交互函数与 main**

在文件末尾追加：

```python
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
    # 先问手机号或邮箱
    choice = _prompt("用 [1] 手机号 还是 [2] 邮箱 查询 open_id? (1/2): ")
    kind = "phone" if choice == "1" else "email"
    value = _prompt("请输入手机号: " if kind == "phone" else "请输入邮箱: ")

    try:
        open_id = resolve_open_id(token, kind, value)
    except RuntimeError as e:
        print(f"✗ {e}")
        return 1

    # 手机号查不到 → 回退到邮箱
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
```

- [ ] **Step 2: 语法检查**

Run: `python3 -m py_compile /Users/mac/.claude-lark/scripts/setup-lark.py && echo OK`
Expected: `OK`

- [ ] **Step 3: 端到端实跑（交互输入真实凭据，用邮箱）**

Run（手动交互）:
```bash
cd /Users/mac/.claude-lark && python3 scripts/setup-lark.py
# App ID: <你的 cli_...>
# App Secret: <你的 secret>
# 选 2（邮箱），输入 pengxjwawa@gmail.com
```
Expected: 依次出现 `✓ token 获取成功`、`✓ open_id: ou_3a1d68eb...`、`✓ 配置已写入 ...`、`✓ hook 已注册`（或已存在跳过）、`✓ 测试消息已发送`，并在 Lark 收到绿色卡片。

- [ ] **Step 4: 赋可执行权限并提交**

```bash
cd /Users/mac/.claude-lark
chmod +x scripts/setup-lark.py
git add scripts/setup-lark.py
git commit -m "feat: interactive main flow for setup-lark"
```

---

## Task 7: 修复其余脚本域名（feishu → larksuite）

**Files:**
- Modify: `scripts/setup.py`
- Modify: `scripts/install.sh`
- Modify: `scripts/install.ps1`
- Modify: `scripts/admin-setup.sh`
- Modify: `.claude/plugins/claude-lark/scripts/setup.py`

- [ ] **Step 1: 批量替换域名**

Run:
```bash
cd /Users/mac/.claude-lark
for f in scripts/setup.py scripts/install.sh scripts/install.ps1 scripts/admin-setup.sh .claude/plugins/claude-lark/scripts/setup.py; do
  python3 -c "
import sys
p='$f'
s=open(p,encoding='utf-8').read()
s=s.replace('open.feishu.cn','open.larksuite.com')
open(p,'w',encoding='utf-8').write(s)
print('patched',p)
"
done
```
Expected: 每个文件打印 `patched ...`。

- [ ] **Step 2: 验证无 feishu.cn 域名残留**

Run: `grep -rn "feishu.cn" /Users/mac/.claude-lark/scripts /Users/mac/.claude-lark/.claude/plugins/claude-lark/scripts`
Expected: 无输出（exit 1）。

- [ ] **Step 3: 语法检查 Python 文件**

Run: `python3 -m py_compile /Users/mac/.claude-lark/scripts/setup.py /Users/mac/.claude-lark/.claude/plugins/claude-lark/scripts/setup.py && echo OK`
Expected: `OK`

- [ ] **Step 4: 提交**

```bash
cd /Users/mac/.claude-lark
git add scripts/setup.py scripts/install.sh scripts/install.ps1 scripts/admin-setup.sh .claude/plugins/claude-lark/scripts/setup.py
git commit -m "fix: pin all installer scripts to larksuite domain"
```

---

## Task 8: 去上游痕迹（ysyecust → pengxjwawa）

**Files:**
- Modify: `.claude-plugin/marketplace.json`
- Modify: `.claude/plugins/claude-lark/.claude-plugin/plugin.json`
- Modify: `scripts/install-remote.sh`
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`
- Delete: `README_en.md`

- [ ] **Step 1: 批量替换仓库标识**

Run:
```bash
cd /Users/mac/.claude-lark
for f in .claude-plugin/marketplace.json .claude/plugins/claude-lark/.claude-plugin/plugin.json scripts/install-remote.sh README.md CONTRIBUTING.md; do
  python3 -c "
p='$f'
s=open(p,encoding='utf-8').read()
s=s.replace('ysyecust/claude-lark','pengxjwawa/claude-lark').replace('\"name\": \"ysyecust\"','\"name\": \"pengxjwawa\"').replace('ysyecust','pengxjwawa')
open(p,'w',encoding='utf-8').write(s)
print('patched',p)
"
done
```
Expected: 每个文件打印 `patched ...`。

- [ ] **Step 2: 删除英文 README**

Run: `cd /Users/mac/.claude-lark && rm -f README_en.md && echo removed`
Expected: `removed`

- [ ] **Step 3: 移除 README 中指向英文版的链接行**

读取 `README.md`，删除形如 `[English](README_en.md)` 的那一行（若存在）。用 Edit 工具精确删除该行。

- [ ] **Step 4: 验证无 ysyecust 残留**

Run: `grep -rn "ysyecust" /Users/mac/.claude-lark --include="*.md" --include="*.json" --include="*.sh" --include="*.ps1" | grep -v docs/superpowers`
Expected: 无输出（exit 1）。（docs/superpowers 下的 spec 提及历史背景，允许保留。）

- [ ] **Step 5: 验证 JSON 合法**

Run: `python3 -c "import json; json.load(open('/Users/mac/.claude-lark/.claude-plugin/marketplace.json')); json.load(open('/Users/mac/.claude-lark/.claude/plugins/claude-lark/.claude-plugin/plugin.json')); print('JSON OK')"`
Expected: `JSON OK`

- [ ] **Step 6: 提交**

```bash
cd /Users/mac/.claude-lark
git add -A
git commit -m "chore: rebrand to pengxjwawa, drop English README"
```

---

## Task 9: 插件 setup-lark 命令对齐新脚本

**Files:**
- Modify: `.claude/plugins/claude-lark/skills/setup-lark.md`

- [ ] **Step 1: 改写 setup-lark.md 指向交互式新脚本**

把 `.claude/plugins/claude-lark/skills/setup-lark.md` 的「Steps」部分整体替换为：

```markdown
## Steps

1. **运行交互式安装器**（它会逐步引导输入 App ID / App Secret / 手机号或邮箱）：

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/setup-lark.py
   ```

   脚本会自动：获取 token → 查询 open_id（手机号查不到会提示改用邮箱）→ 写入 `~/.config/claude-lark/config.json`（权限 600）→ 幂等注册 Claude Code hook → 发送测试消息。

2. **报告结果**：
   - 全部 `✓` → 安装完成，请用户到 Lark 查收测试卡片
   - 出现 `✗` → 按提示排查：
     - token 失败 → App ID / App Secret 错误，或不是 Lark 国际版应用
     - `99991672` → 应用缺权限（`contact:user.id:readonly` / `im:message:send`），需到 Lark 后台开通并发版
     - 查不到 open_id → 用户不在应用可用范围内，或该手机号未在组织绑定（改用邮箱）

## Important Notes

- **不要回显 App Secret**
- 配置文件位于 `~/.config/claude-lark/config.json`（权限 600）
- 仅支持 Lark 国际版（open.larksuite.com）
```

- [ ] **Step 2: 提交**

```bash
cd /Users/mac/.claude-lark
git add .claude/plugins/claude-lark/skills/setup-lark.md
git commit -m "docs: point setup-lark plugin command to new interactive script"
```

---

## Task 10: 清除 git 历史，重新初始化并推送

> ⚠️ 本任务会清掉当前所有 git 历史（含前述各 commit），这是用户选定的"干净初始提交"预期行为。**Step 5 的推送为对外发布操作，执行到该步时先把命令交给用户、确认后再推。**

**Files:**
- 全仓库

- [ ] **Step 1: 确认 GitHub 空仓库已就绪**

提醒用户：在 GitHub 网页创建空仓库 `pengxjwawa/claude-lark`（不要勾选 README/.gitignore/License，保持空）。等待用户确认已创建。

- [ ] **Step 2: 确认 .gitignore 含 .omc/ 等本地目录**

Run: `grep -q "^.omc" /Users/mac/.claude-lark/.gitignore 2>/dev/null && echo "has .omc" || echo "need add"`
若输出 `need add`，向 `.gitignore` 追加一行 `.omc/`。

- [ ] **Step 3: 清除历史并重新 init**

Run:
```bash
cd /Users/mac/.claude-lark
rm -rf .git
git init -q
git add -A
git status -s | head -30
```
Expected: 列出待提交文件，确认不含 `.omc/`、`config.json` 等敏感/本地文件。

- [ ] **Step 4: 创建干净初始提交**

```bash
cd /Users/mac/.claude-lark
git branch -M main
git commit -q -m "Initial commit: claude-lark for Lark (international)"
git log --oneline
```
Expected: 仅一条 `Initial commit ...`。

- [ ] **Step 5: 关联远程并推送（对外发布，先确认）**

把以下命令交给用户、确认后再执行：
```bash
cd /Users/mac/.claude-lark
git remote add origin https://github.com/pengxjwawa/claude-lark.git
git push -u origin main
```
Expected: 推送成功，GitHub 上出现该仓库内容。

---

## Self-Review 记录

- **Spec 覆盖**：① Lark-only 域名固定 → Task 1/7；② 去上游痕迹 → Task 8；③ setup-lark.py（含手机号→邮箱回退）→ Task 2-6；④ 插件命令对齐 → Task 9；⑤ 干净历史+推送 → Task 10；⑥ 错误打印真实 code+msg → Task 3 的 RuntimeError 信息 + send_test 的 WARN。全部有对应任务。
- **占位符**：无 TBD/TODO，所有代码步骤含完整代码。
- **类型/命名一致**：`get_token`、`resolve_open_id`、`write_config`、`send_test`、`register_hook`、`_api_post`、`_settings_path`、`_prompt`、`main` 在各任务间引用一致；config 字段 `app_id/app_secret/open_id/events` 一致；NOTIFY_PATH 指向 `~/.claude-lark/claude_lark_notify.py` 与 hook 命令一致。
