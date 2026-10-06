# lark-ask

**飞书知识问答（Lark Ask AI / ask.larksuite.com）MCP 工具集**

无需 API Key，复用浏览器登录态，通过 protobuf gateway 直接对接飞书 IM 后端。现已以纯 TypeScript 集成到 `feishu-lark-cli` 中。

## 它做什么

- `feishu_lark_ask` — 向飞书 AI 提问，获取回答（支持追问、联网搜索开关、JSON 输出）
- `feishu_lark_ask_topics` — 列出/查看历史话题
- `feishu_lark_ask_auth_check` — 检查浏览器登录态

## 工作原理

```
[TS] 构造 PutAIRoundRequest protobuf
   ↓ base64
[playwright-cli eval] 在 ask.larksuite.com 页面上下文里 fetch()
   ↓ 浏览器自动注入 Cookie 和必需的身份头
[Lark IM Gateway] /im/gateway/ 返回 protobuf
   ↓ base64
[TS] 解包 → 轮询 PULL_AI_ROUNDS_BY_ID 直到 FINISH
```

走浏览器代理而非直接 HTTP，是因为 ask.larksuite.com 的关键登录 cookie 是 HttpOnly 的，无法通过常规 HTTP 客户端读取或发送。

## 前置依赖

| 依赖 | 说明 |
|------|------|
| `playwright-cli` + Playwright MCP Bridge 扩展 | 浏览器代理，复用登录态 |
| 浏览器已登录 https://ask.larksuite.com/ | 飞书知识问答的登录态 |

## 使用示例

```json
// 提问（默认开启联网搜索）
{ "tool": "feishu_lark_ask", "query": "今天有什么新闻" }

// 在已有话题内追问
{ "tool": "feishu_lark_ask", "topic": 7634xxx, "query": "继续讲讲安全机制" }

// 关闭联网搜索
{ "tool": "feishu_lark_ask", "no_web": true, "query": "私域问题" }

// JSON 输出（含引用列表）
{ "tool": "feishu_lark_ask", "json": true, "query": "X" }

// 列出最近话题
{ "tool": "feishu_lark_ask_topics", "action": "list", "limit": 10 }

// 查看话题详情
{ "tool": "feishu_lark_ask_topics", "action": "get", "topic_id": 7634xxx, "rounds": 5 }

// 检查登录态
{ "tool": "feishu_lark_ask_auth_check" }
```

## 文件结构

```
lark-ask/
├── README.md                    # 本文件
├── SKILL.md                     # Claude Code 技能元数据 + 命令速查
├── references/                  # 协议文档
│   ├── gateway-protocol.md      # gateway 协议说明（含必需 header 列表）
│   ├── commands.md              # 122 条 LARK_AI_KNOWLEDGE_* 命令清单
│   └── proto-schema.md          # 关键消息字段说明
└── scripts/_proto/              # （历史文件）protoc 生成的 *_pb2.py
```

> 注意：运行时不再依赖 Python。`proto-descriptors.bin` 已嵌入 `feishu-lark-cli` 的 `src/tools/lark-ask/` 目录中，由 `protobufjs` 直接加载。

## 关键技术细节

详见 `references/gateway-protocol.md`。最重要的几点：

1. **必须带 6 个 web 客户端身份头**（`x-appid: 1161` / `x-command: <cmd>` / `x-source: web` 等），缺任一个会被服务端误导性地拒绝（返回 "The server is busy" 而非 401）
2. **AIAnswer.content 是二级 protobuf**（AnswerCard 序列化后的 bytes），主答案在 `rag_answer_block.markdown`
3. **联网搜索开关**藏在 `qa_ai_topic_request_info` 这个 passthrough bytes 里（field 4 是 enabled-features 的 repeated int32），ON/OFF 的 magic bytes 见 TS 源码

## 限制

- 仅支持主对话场景（ASK_SCENE_MAIN_TOPIC）
- 不实现长连接 `PULL_PACKETS_BY_SIDS`，用拉式轮询代替
- 不支持文件上传 / 多 Agent 切换 / 知识库 CRUD
- 答案直接返回 Markdown 源码，不做终端美化渲染

## 协议来源

- `lark/im-protobuf` 仓库的 IDL（公司内部）
- `byteapi/feishu/gateway.go` 的 makePacket / parseResponse 实现参考
