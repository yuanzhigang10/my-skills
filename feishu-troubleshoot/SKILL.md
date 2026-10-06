---
name: feishu-troubleshoot
description: |
  feishu-lark 问题排查指南。包含常见问题 FAQ 和诊断方法。
---

# feishu-lark 问题排查

## 常见问题

### Bot mode 里工具消失或 feishu_auth 不可用

**现象**：`feishu-lark --auth-mode bot list` 看不到大部分工具，或调用 `feishu_auth` 返回不可用。

**原因**：bot mode 明确禁止读取、恢复或申请用户授权，只展示 bot-safe 工具。user-only 工具（读取消息、日历、表格、任务、搜索文档等）会隐藏，直接调用会得到明确错误。

**解决**：

- 需要纯机器人/应用身份：继续用 `--auth-mode bot`，改用 `feishu_card`、`feishu_create_doc {"as":"bot"}`、`feishu_im_user_message {"send_as":"bot"}` 等 bot-safe 工具
- 需要读取用户资源：切回 `--auth-mode user`，运行 `feishu-lark auth`

```bash
feishu-lark --auth-mode bot list
feishu-lark --auth-mode user auth
```

### "需要用户授权" 错误

**现象**：调用工具返回 `需要用户授权。请先运行 feishu_auth 工具完成飞书登录授权。`

**解决**：

1. 运行 `feishu-lark auth` 完成认证
2. 认证成功后设置环境变量：`export FEISHU_USER_OPEN_ID=<返回的 ou_xxx>`
3. 重新调用工具

### "应用缺少权限" 错误

**现象**：`应用缺少权限 [xxx]，请管理员在飞书开放平台为应用开通相应权限。`

**解决**：

1. 登录 https://open.feishu.cn/app
2. 选择应用 → 权限管理
3. 搜索并开通缺失的权限
4. 创建新版本 → 审核 → 发布
5. 重新运行 `feishu-lark auth` 授权新权限

### Token 过期

**现象**：之前能用的工具突然报授权错误

**解决**：

```bash
# 重新认证
feishu-lark auth
```

Token 有效期约 2 小时，refresh token 有效期约 30 天。feishu-lark 会自动刷新，但 refresh token 过期后需要重新认证。

### Error code 20027 (敏感权限)

**现象**：认证时报错 `Missing permissions detected... im:message.send_as_user`

**原因**：`im:message.send_as_user` 是敏感用户权限，默认 scope 申请已自动过滤。发送消息现在默认以机器人身份（`send_as=bot`）发送，不再需要此权限。如仍需以用户身份发送，需手动指定 scope。

**解决**：

- 默认方案：使用 `send_as=bot`（默认），无需额外权限
- 如需用户身份发送：手动指定 scope 认证

```bash
feishu-lark auth "im:message im:message.send_as_user"
```

### feishu_magic_doc 在 bot mode 下提示 botRuntime.magic.enabled=false

**现象**：调用 `feishu_magic_doc {"as":"bot"}` 返回 `botRuntime.magic.enabled=false`。

**原因**：妙笔 HTML Box 写入属于 bot runtime 能力，bot mode 下默认可见但不可执行，需要显式开启。

**解决**：

```bash
FEISHU_BOT_MAGIC_ENABLED=true feishu-lark --auth-mode bot call feishu_magic_doc '{"action":"create","as":"bot","title":"Demo","html":"<html><body>ok</body></html>"}'
```

或在 profile 中写：

```json
{
  "authMode": "bot",
  "botRuntime": {
    "magic": { "enabled": true, "allowPersonalToken": false }
  }
}
```

### git diff / code review 卡片校验失败

**现象**：`feishu_card` 返回 `git_diff_review/code_review 严格模式需要真实详情入口`。

**原因**：`doc_url` 只是完整说明文档，不是可查看真实 diff/review 的详情页。严格模式要求传 `side_panel_url`、`detail_url`、`diff_url` 或 `detail_url_template`。

**解决**：给卡片传真实可打开的详情页，PC 会通过 Feishu AppLink 在右侧栏打开。

```json
{
  "answer_type": "git_diff_review",
  "doc_url": "https://...",
  "side_panel_url": "https://your-review-page/detail?id=123",
  "side_panel_button_text": "右侧看 Diff"
}
```

### 无法获取 user_open_id

**现象**：认证成功但返回 `无法从 access_token 中提取 user_open_id`

**解决**：这通常是网络问题。feishu-lark 通过飞书 userinfo API 获取 open_id，确保网络可以访问 `open.feishu.cn`。

---

## 调试日志

如需查看 API 调用完整链路（包括 UAT、请求体、响应状态），可开启 debug 日志：

### 常规 debug（敏感信息自动掩码）

```bash
# CLI 模式
feishu-lark --verbose call feishu_lark_parser '{"url":"..."}'

# MCP 模式
export DEBUG=1
```

### 完整复现日志（不过滤 token 和请求体）

**⚠️ 注意：仅用于本地问题复现，不要共享包含完整 token 的日志。**

```bash
# CLI 模式
DEBUG_UNSAFE=1 feishu-lark --verbose call feishu_lark_parser '{"url":"..."}'

# MCP 模式
export DEBUG_UNSAFE=1
export DEBUG=1
```

开启后 stderr 会输出：

- 请求方法、URL、Headers（含完整/掩码 token）
- 请求 body / args
- 响应状态码
- LarkParser / MCP Gateway / Feishu OAPI 的调用详情

---

## 诊断步骤

### 1. 检查环境变量

```bash
echo $FEISHU_APP_ID
echo $FEISHU_APP_SECRET
echo $FEISHU_USER_OPEN_ID
echo $FEISHU_AUTH_MODE
```

### 2. 检查认证状态

```bash
feishu-lark call feishu_get_user '{}'
```

如果返回用户信息，说明认证正常。如果报错，需要重新认证。

### 3. 列出可用工具

```bash
feishu-lark list
```

### 4. 检查 Token 存储

Token 存储在系统 Keychain 中，service name 为 `openclaw-feishu-uat`：

```bash
# macOS
security find-generic-password -s "openclaw-feishu-uat" -a "${FEISHU_APP_ID}:${FEISHU_USER_OPEN_ID}" 2>&1 | head -5
```

---

## 权限速查

| 功能域                  | 常用权限                                                        |
| ----------------------- | --------------------------------------------------------------- |
| 日历                    | `calendar:calendar:read`, `calendar:calendar.event:create`      |
| 任务                    | `task:task:read`, `task:task:write`                             |
| 文档                    | `docx:document:readonly`, `docx:document:write_only`            |
| 表格                    | `sheets:spreadsheet:read`, `sheets:spreadsheet:write_only`      |
| 多维表格                | `base:app:read`, `base:record:retrieve`                         |
| 消息（读取）            | `im:message:readonly`, `im:chat:read`                           |
| 消息（发送，bot 默认）  | `im:message`（应用权限）                                        |
| 消息（发送，user 身份） | `im:message`, `im:message.send_as_user`（敏感权限，需手动授权） |
| 通讯录                  | `contact:user.base:readonly`                                    |
| 知识库                  | `wiki:node:read`, `wiki:space:retrieve`                         |
| 搜索                    | `search:docs:read`, `search:message`                            |
