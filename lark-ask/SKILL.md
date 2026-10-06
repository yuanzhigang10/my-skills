---
name: lark-ask
description: 飞书知识问答（ask.larksuite.com / Lark Ask AI）MCP 工具集。直接在 Claude Code 里向飞书 AI 提问、查看历史话题、检查登录态。当用户提到"问飞书 AI"、"问 Lark AI"、"飞书知识问答"、"ask larksuite"、"lark ask"、"问下飞书"、"飞书 AI 助理"、"Lark AI 帮我查"、"知识库问答"时使用。即使用户没有明确说出"用 lark-ask 技能"，只要问题是想交给飞书内部的 AI 助理来回答（区别于 Claude 自己回答），就应该用本技能而不是 WebFetch ask.larksuite.com。
---

# lark-ask — 飞书知识问答 MCP 工具

向 ask.larksuite.com 直接发起 protobuf 调用，复用浏览器登录态，无需任何 API Key。

## 触发场景

| 用户说 | 工具 |
|--------|------|
| "问下飞书 AI: XXX" / "用 lark ask 查一下 XXX" | `feishu_lark_ask` |
| "在话题 7634xxx 内追问 YYY" | `feishu_lark_ask` (传 topic=7634xxx) |
| "看下我最近的 lark ask 历史" | `feishu_lark_ask_topics` (action=list) |
| "把话题 7634xxx 的对话拉出来" | `feishu_lark_ask_topics` (action=get, topic_id=7634xxx) |
| "lark ask 登录态还在吗" | `feishu_lark_ask_auth_check` |

## 命令速查

```json
// 1) 一次性提问（默认开启联网搜索）
{ "tool": "feishu_lark_ask", "query": "帮我介绍一下飞书" }

// 2) 在已有话题内追问
{ "tool": "feishu_lark_ask", "topic": 7634xxx, "query": "继续讲讲安全机制" }

// 3) 关闭联网搜索（仅用知识库）
{ "tool": "feishu_lark_ask", "no_web": true, "query": "私域问题" }

// 4) JSON 输出（含引用列表）
{ "tool": "feishu_lark_ask", "json": true, "query": "X" }

// 5) 列最近话题
{ "tool": "feishu_lark_ask_topics", "action": "list", "limit": 10 }

// 6) 看话题详情 + 最近 5 轮对话
{ "tool": "feishu_lark_ask_topics", "action": "get", "topic_id": 7634xxx, "rounds": 5 }

// 7) 检查浏览器登录态
{ "tool": "feishu_lark_ask_auth_check" }
```

## 工作原理

```
[TS] PutAIRoundRequest → 序列化为 improto.Packet
   ↓ base64
[playwright-cli eval]  fetch('/im/gateway/', body=bytes, credentials='include')
   ↓ 浏览器自动带 ask.larksuite.com 的 Cookie
[Lark IM Gateway 后端] 返回 protobuf Packet
   ↓ base64
[TS] 解包 → AIRound + 轮询 PullAIRoundsByID 直到 FINISH
```

- 网络层走 CLI 自管的 **headless chromium**，无需用户手动启动浏览器
- 协议层是 Lark IM 内部 protobuf gateway，复用 IM 长连接管子做 AI 流式
- 轮询策略：每 0.6s 主动 pull `PULL_AI_ROUNDS_BY_ID`（cmd 1110006），直到状态为 FINISH / STOPPED / ERROR

## 前置依赖

| 依赖 | 检查 | 缺失时 |
|------|------|--------|
| Playwright chromium | 首次运行 `feishu-lark ask login` 时自动下载 (~120MB) | `npx playwright install chromium` |
| ask.larksuite.com 登录态 | `feishu_lark_ask_auth_check` | 运行 `feishu-lark ask login`，终端渲染二维码扫描即可 |

## 登录 / 登出

```bash
feishu-lark ask login    # headless 启动，终端渲染二维码，用飞书 App 扫码
feishu-lark ask logout   # 清除本机 ask 会话
```

登录态（cookie + localStorage）加密保存到和飞书 UAT 同一套存储（macOS keychain / Linux/Windows 加密文件）。过期后任一 tool 调用会报 `NotLoggedIn`，重跑 `ask login` 即可。

## 错误处理

| 场景 | 含义 | 处理 |
|--------|------|--------|
| 返回 FINISH | 正常结束 | — |
| 返回 STOPPED | 用户主动停止 | — |
| 返回 ERROR | 完成但 status=ERROR | 看返回的 error_msg |
| 未登录（NotLoggedIn） | storage state 缺失或过期 | 运行 `feishu-lark ask login` |
| Gateway 错误 | headless 启动失败 / 网络中断 | 检查网络；`npx playwright install chromium` 重装 |
| Lark 业务错误（HTTP 900） | 服务端拒绝 | 看返回的 LarkError code |

## 引用与拓展

- 协议参考：`references/gateway-protocol.md`
- 命令枚举：`references/commands.md`（122 条 LARK_AI_KNOWLEDGE_*）
- 关键消息 schema：`references/proto-schema.md`

## 不在 v1 范围

- 长连接 `PULL_PACKETS_BY_SIDS`（用拉式轮询代替）
- 文件上传 / 知识库管理 / Agent 选择
- 答案 Markdown 渲染美化（直接打印纯 Markdown 文本）
