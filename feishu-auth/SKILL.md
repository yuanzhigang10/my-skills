---
name: feishu-auth
description: |
  飞书 OAuth 认证。使用 feishu-lark CLI 进行 Device Flow 认证，管理 User Access Token。
  当用户首次使用飞书工具、遇到权限错误、需要重新授权时使用。
---

# 飞书认证 (feishu-auth)

## 认证流程

feishu-lark 支持两种认证方式：

> `authMode=bot` 时不会注册 `feishu_auth`，也不会读取 UAT / last-user。需要 OAuth 或用户态工具时先切回 `--auth-mode user`；需要纯机器人/应用身份时使用 `--auth-mode bot` 和 bot-safe 工具。

### 方式一：OAuth Device Flow（默认）

```bash
feishu-lark auth
```

会输出授权链接到 stderr，自动打开浏览器。用户在浏览器中完成授权后，CLI 会自动获取 token 并存储。

返回 JSON：
```json
{
  "status": "authorized",
  "user_open_id": "ou_xxx",
  "scope": "calendar:calendar:read ..."
}
```

### 方式二：动态 UAT（直接传入 User Access Token）

适用于已有 token、CI/CD 环境或临时调试场景，跳过 OAuth 认证流程。

**CLI 方式：**
```bash
# 通过 --UAT 参数
feishu-lark --UAT u-xxxxx call feishu_fetch_doc '{"url":"..."}'

# 通过环境变量
FEISHU_UAT=u-xxxxx feishu-lark call feishu_fetch_doc '{"url":"..."}'
```

**MCP 方式（推荐）：**
调用 `feishu_auth` 工具时传入 `uat` 参数，后续所有工具自动使用：
```json
{ "uat": "u-xxxxx" }
```

> 动态 UAT 不支持自动刷新。Token 过期后需重新传入有效 token。

### 检查现有认证

设置环境变量 `FEISHU_USER_OPEN_ID` 后，CLI 会自动使用已有 token：
```bash
export FEISHU_USER_OPEN_ID=ou_xxx
feishu-lark call feishu_get_user '{}'
```

### 指定 scope 认证

```bash
feishu-lark auth "calendar:calendar:read task:task:read"
```

### Bot mode（不走用户授权）

```bash
FEISHU_AUTH_MODE=bot feishu-lark list
feishu-lark --auth-mode bot call feishu_card '{"action":"validate","source":{"type":"raw","card":{"schema":"2.0","body":{"elements":[]}}}}'
```

bot mode 只展示 bot-safe 工具，典型包括：

- `feishu_card`：机器人/应用身份发送或回复卡片
- `feishu_create_doc {"as":"bot"}`：机器人/应用身份创建基础 docx
- `feishu_magic_doc {"as":"bot"}`：默认禁用，需 `botRuntime.magic.enabled=true`
- `feishu_im_user_message {"send_as":"bot"}`：机器人身份发普通消息

在 bot mode 下传 `send_as=user`、调用 user-only 工具或运行 `feishu_auth` 都会明确失败。

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `FEISHU_APP_ID` | 否 | 飞书应用 App ID（不设则使用内置默认应用） |
| `FEISHU_APP_SECRET` | 否 | 飞书应用 App Secret（不设则使用内置默认应用） |
| `FEISHU_BRAND` | 否 | `feishu`（默认）或 `lark` |
| `FEISHU_USER_OPEN_ID` | 否 | 预设用户 ID，跳过认证 |
| `FEISHU_UAT` | 否 | 直接提供 User Access Token，跳过 OAuth |
| `FEISHU_AUTH_MODE` | 否 | `user`（默认）或 `bot`；bot 模式不读取/申请用户授权 |
| `FEISHU_CONFIG` | 否 | 配置文件路径 |
| `FEISHU_PROFILE` | 否 | Profile 名称 |

> 也可通过配置文件管理凭据（支持多应用 profiles），详见 feishu-setup。

## 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| "需要用户授权" | 未认证或 token 过期 | 运行 `feishu-lark auth` |
| `authMode=bot，feishu_auth 不可用` | 当前处于 bot mode | 切换 `--auth-mode user` 后再认证 |
| `authMode=bot，禁止使用用户授权调用` | bot mode 调用了 user-only 工具 | 改用 bot-safe 工具或切回 user |
| "应用缺少权限" | 应用未在开放平台开通权限 | 在飞书开放平台为应用开通对应权限 |
| Error code 20027 | scope 包含敏感权限 | 发送消息默认使用 bot 身份，无需 `im:message.send_as_user`。如仍触发，手动指定 scope 排除敏感权限 |

## Token 共享

feishu-lark 和 openclaw-lark 共享同一个 Keychain service name（`openclaw-feishu-uat`），任一方授权后另一方可直接使用。
