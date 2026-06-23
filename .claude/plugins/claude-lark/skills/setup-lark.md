---
name: setup-lark
description: Configure claude-lark notifications. Use when user wants to set up or reconfigure Lark/Feishu notifications for Claude Code.
user-invocable: true
---

# Setup claude-lark Notifications

Help the user configure claude-lark to receive Lark (Feishu) notifications.

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
