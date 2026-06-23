# claude-lark Lark-only 私有化封装设计

日期：2026-06-23
状态：已确认设计，待实现
目标仓库：`github.com/pengxjwawa/claude-lark`

## 目标

把当前从 `ysyecust/claude-lark` 派生的代码，封装成 **pengxjwawa 自己的、只支持 Lark 国际版** 的项目，用干净的初始提交（不含上游历史）推送到自己的 GitHub，并附带一个一键安装脚本 `setup-lark.py`。

## 背景

现有上游代码全部写死 `open.feishu.cn`（国内飞书），而实际使用的是 Lark 国际版 `open.larksuite.com`，两套系统物理隔离、open_id 命名空间不通用。直接用上游安装会导致 `cross app` / 权限错误。本次封装把项目固定为 Lark-only，并补上一键安装体验。

## 1. Lark-only 精简

- 域名**固定** `open.larksuite.com`，写进 `claude_lark_notify.py`（已改）与新 `setup-lark.py`。
- 现有 `scripts/setup.py`、`scripts/install.sh`、`scripts/install.ps1` 中所有写死 `feishu.cn` 的 API 域名，统一改为 `larksuite.com`。
- 不引入"双域名探测"逻辑——只服务 Lark，探测属多余复杂度（YAGNI）。

## 2. 去上游痕迹（`ysyecust` → `pengxjwawa`）

- `.claude-plugin/marketplace.json`：`owner.name` → `pengxjwawa`。
- `scripts/install-remote.sh`：`REPO_URL` 与示例 `curl` 命令 → `pengxjwawa/claude-lark`。
- `README.md`：所有 `ysyecust/claude-lark` 引用、安装命令、徽章链接 → `pengxjwawa/claude-lark`。
- **删除 `README_en.md`**：只保留中文 README。

## 3. 新增 `scripts/setup-lark.py`（Lark-only 一键安装）

单文件、零依赖（仅标准库）。流程：

1. 交互输入 App ID / App Secret。
2. 交互输入手机号**或**邮箱（二选一）。
3. 固定 `open.larksuite.com` 域名获取 `tenant_access_token`。
4. 调 `batch_get_id` 查 open_id；**用手机号查无结果时不退出，提示改用邮箱并允许重新输入重试**。
5. 写 `~/.config/claude-lark/config.json`（字段 `app_id`/`app_secret`/`open_id`/`events`，权限 `0600`）。
6. 幂等注册 hook 到 `${CLAUDE_CONFIG_DIR:-~/.claude}/settings.json`：hook 命令指向 `~/.claude-lark/claude_lark_notify.py`；写前备份为 `settings.json.bak`；已存在指向同脚本的 Stop/Notification hook 则跳过；不修改其他 hook（如 rtk）。
7. 发测试卡片，失败时打印 Lark 返回的真实 `code`+`msg`。

> 注：因项目已固定 Lark-only，notify 脚本域名直接固定 larksuite，config **不需要** `domain` 字段（与早期双域名设计不同，此处简化）。

## 4. 插件命令对齐

- `.claude/plugins/claude-lark` 下的 `/setup-lark` 命令改为调用新的 Lark-only `setup-lark.py`，使插件安装路径与一键脚本行为一致。

## 5. 干净历史 + 推送

- `rm -rf .git && git init`（清除上游 commit 关联）。
- 把改好的全部文件作为**首次提交**。
- `git remote add origin https://github.com/pengxjwawa/claude-lark.git`。
- `git push -u origin main`。
- **前提**：用户需先在 GitHub 网页创建空仓库 `pengxjwawa/claude-lark`（脚本无法替用户创建远程仓库）。
- **推送为对外发布操作**：实现阶段会先把命令交给用户、确认后再推，不自动推送。

## 6. 错误处理与测试

- 所有 API 失败打印 Lark 真实 `code`+`msg`（不吞成笼统的 `HTTP 400`）。
- 验证：本机实跑 `setup-lark.py` 一次——邮箱查到 open_id、config 正确写入、hook 幂等注册、收到测试卡片。
- 幂等验证：连跑两次，第二次不重复添加 hook，且 rtk hook 保持不变。
- 回退验证：故意用查不到的手机号，确认提示改用邮箱而非直接退出。

## 范围之外（YAGNI）

- 不做飞书国内版兼容。
- 不重写卸载逻辑（保留现有 `uninstall.sh`，仅按需把其中 feishu 域名改 larksuite——若有）。
- 不新增远程 `curl | bash` 以外的分发形态。
- 不保留英文 README。
