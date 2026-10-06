---
name: feishu-setup
description: |
  feishu-lark CLI 安装与配置指南。当用户首次使用飞书相关工具、提示找不到 feishu-lark 命令、
  或需要配置飞书应用凭据时使用。
---

# feishu-lark 安装与配置

## 安装 CLI

```bash
npm install -g @i18n-ecom/feishu-lark-mcp-server --registry=https://bnpm.byted.org/
```

安装后可用两个命令：

- `feishu-lark-mcp-server` — MCP stdio 服务（供 Claude Code / MCP 客户端自动调用）
- `feishu-lark` — CLI 工具（手动调用工具、认证等）

## 环境变量配置

> 内置默认飞书应用凭据，无需额外配置即可使用。如需使用自定义应用，可通过环境变量或配置文件覆盖。

| 变量                  | 必填 | 说明                                          |
| --------------------- | ---- | --------------------------------------------- |
| `FEISHU_APP_ID`       | 否   | 飞书应用 App ID（不设则使用内置默认应用）     |
| `FEISHU_APP_SECRET`   | 否   | 飞书应用 App Secret（不设则使用内置默认应用） |
| `FEISHU_BRAND`        | 否   | `feishu`（默认）或 `lark`                     |
| `FEISHU_USER_OPEN_ID` | 否   | 预设用户 ID，跳过交互式认证                   |
| `FEISHU_UAT`          | 否   | 直接提供 User Access Token，跳过 OAuth        |
| `FEISHU_AUTH_MODE`    | 否   | `user`（默认）或 `bot`；bot 模式不读取/申请用户授权 |
| `FEISHU_CONFIG`       | 否   | 配置文件路径，等同于 `--config` 参数          |
| `FEISHU_PROFILE`      | 否   | Profile 名称，选择配置文件中的指定 profile    |
| `FEISHU_SCOPE`        | 否   | 自定义 OAuth 授权 scope（空格分隔）           |

## 配置文件

也可通过 JSON 配置文件管理凭据（推荐用于自定义应用）：

创建 `feishu-lark.config.json`：

```json
{
  "appId": "your_app_id",
  "appSecret": "your_app_secret"
}
```

```bash
feishu-lark --config ./feishu-lark.config.json serve
```

未指定时会自动查找 `./feishu-lark.config.json`、`./.feishu-lark.json`、`~/.feishu-lark.json`。环境变量优先级高于配置文件。

管理多个飞书应用时，可使用 profiles：

```json
{
  "defaultProfile": "work",
  "docPermissionPolicy": {
    "enabled": true,
    "sensitivityLevel": "L2",
    "linkShareEntity": "tenant_editable",
    "manageCollaboratorEntity": "collaborator_can_edit"
  },
  "botRuntime": {
    "magic": { "enabled": false, "allowPersonalToken": false },
    "tos": { "allowAnonymousUpload": true, "allowMultipartUpload": false },
    "cardCallback": { "enabled": false }
  },
  "cardDefaults": {
    "sidebar": {
      "applinkDomain": "https://applink.feishu.cn",
      "mode": "sidebar-semi",
      "maxWidth": 1000
    }
  },
  "profiles": {
    "work": { "appId": "cli_work_xxx", "appSecret": "secret_work", "authMode": "user" },
    "personal": {
      "appId": "cli_personal_xxx",
      "appSecret": "secret_personal",
      "brand": "lark",
      "scope": "docx:document bitable:app"
    }
  }
}
```

> `scope` 字段可选，用于自定义 `feishu-lark auth` 默认申请的 OAuth 权限范围；未设置时按所有已注册工具的非敏感权限申请。优先级：CLI 参数 > `FEISHU_SCOPE` > profile `scope` > 默认全量。
>
> `authMode` 默认是 `user`。如果某个 profile 写了 `"authMode":"bot"`，`serve/list/call` 会保持 bot mode；顶层 `authMode` 不会自动继承到所有 profile。顶层只适合放 `docPermissionPolicy`、`botRuntime`、`cardDefaults` 这类共享默认块。

```bash
feishu-lark --config ./config.json --profile personal auth
# 或
FEISHU_PROFILE=personal feishu-lark auth
```

### 快速切换默认 profile

```bash
feishu-lark --config ./config.json profiles set-default personal
```

设置后无需再每次指定 `--profile`， CLI 会自动使用新默认 profile。

### 登出

```bash
feishu-lark logout             # 登出当前 profile 对应用户（交互确认）
feishu-lark logout --yes       # 跳过确认
feishu-lark logout --all       # 清除本机所有飞书 CLI 登录凭据
feishu-lark logout --all --yes # 不确认直接清空
```

`logout` 只清除认证凭据（macOS keychain / Linux / Windows 加密存储中的 token 与 last-user 映射），不会动配置文件。

## 自动创建机器人

如果没有飞书应用，可一键创建：

```bash
feishu-lark init
```

打开输出的链接完成确认后，App ID 和 Secret 会自动写入 `~/.feishu-lark.json`。指定 `--config` 时写入指定路径。

`init` 新增的 profile 会显式写入默认 runtime 配置块，方便审计；但认证模式仍默认 `user`，需要纯机器人运行时请显式设置 `authMode:"bot"` 或使用 `--auth-mode bot`。

## 验证安装

```bash
feishu-lark auth        # 完成 OAuth 认证
feishu-lark list        # 列出所有可用工具
feishu-lark call feishu_get_user '{}'   # 测试调用

# bot mode 验证：不注册 feishu_auth，只展示 bot-safe 工具
feishu-lark --auth-mode bot list
```

## Agent CLI 使用最佳实践

### 工具发现

```bash
# 列出所有可用工具
feishu-lark list --json

# 查看工具参数定义（推荐在首次调用前使用）
feishu-lark describe feishu_create_doc
```

### 调用工具

```bash
# 推荐：使用 call 命令 + JSON 参数
feishu-lark call feishu_create_doc '{"title":"标题","markdown":"# 内容"}'

# 也支持 flag 风格
feishu-lark call feishu_get_user --action=me
```

### 错误处理

- 退出码 0 = 成功
- 退出码 1 = 运行时错误（如 API 失败）
- 退出码 2 = 用法错误（如未知命令）
- 工具调用结果以 JSON 输出到 stdout，错误信息输出到 stderr

## 可选：meegle 支持（飞书项目 / Lark Project）

如果要用 `feishu_meegle` tool 调用 Meegle（管理工作项、跑 MQL 查询、建需求+任务），需要额外装 `@lark-project/meegle` 子 CLI。`@lark-project/meegle` 在 `optionalDependencies` 中，**不装也不影响其他 feishu-lark 工具**。

### 安装

```bash
npm install -g @lark-project/meegle
```

### 配置与登录

```bash
meegle config set host meego.larkoffice.com    # 或 project.feishu.cn 等
meegle auth login --device-code                # AI agent / 无 TTY 必须 --device-code
meegle auth status                              # 验证
```

也可以让 AI 代查：

```ts
feishu_meegle({ action: "auth_status" })
```

返回 `installed: false` 给你装机提示；`logged_in: false` 提示登录。

### 项目默认参数

建需求 / 任务时业务线、项目、模板、负责人等可以配在项目根 `./.feishu-lark/meego.json`：

```json
{
  "projectKey": "<空间 key>",
  "businessOptionId": "<业务线 cascade 叶子 id>",
  "projectWorkitemId": "<项目工作项 ID>",
  "templateId": "<模板 option_id>",
  "assigneeUserKey": "<默认负责人 userkey>",
  "nodeKey": "started"
}
```

或用 `FEISHU_LARK_MEEGO_*` 环境变量（旧 `MEEGO_*` / meegle 原生 `MEEGLE_*` 也兼容）。字段含义见 `feishu-meegle` skill。
