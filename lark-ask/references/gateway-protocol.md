# Lark IM Gateway Protocol（/im/gateway/）

## 端点

```
POST https://internal-api-lark-api.larksuite.com/im/gateway/
Content-Type: application/x-protobuf
Cookie: <浏览器自动带>
Body: 序列化的 improto.Packet

# 业务命令必须额外带这 6 个 web 客户端身份头，否则服务端拒绝并返回
# AIRoundStatus=ERROR + error_msg="The server is busy. Please try again later."
locale: zh-CN
x-appid: 1161
x-command: <cmd 数字，必须与 packet.cmd 一致>
x-command-version: 100.0.0
x-source: web
x-web-version: 100.0.0
```

## ⚠️ 关键陷阱：缺 header 时服务端的"server busy"是误导性错误

`byteapi/feishu/gateway.go` 只设了 `content-type` 和 `x-request-id`，对它原本调的接口够用；但 ask.larksuite.com 的 `LARK_AI_KNOWLEDGE_*` 类命令需要完整的 web 客户端身份头。缺任何一个上面的 header，服务端不会返回 401/403，而是接受请求 → 创建 Round → 立刻把 Round 标记为 `status=ERROR` + `error_msg="The server is busy. Please try again later."`。

排查时千万别被这个错误信息坑：它不是限流、不是配额、不是请求体字段缺失。只要装个 fetch 拦截器抓真实 web 请求的 `options.headers` 对比一下就能定位。

## Packet 外层（improto.Packet，improto.proto）

| 字段 | 类型 | 说明 |
|------|------|------|
| sid | string | session uuid |
| payload_type | enum | 固定 PB2=1 |
| **cmd** | enum Command | **决定 payload 的具体消息类型** |
| status | uint32 | 请求侧填 1；响应侧 200/900 等 |
| payload | bytes | 内层 protobuf |
| cid | string | correlation uuid |

参考 Go 实现：`code.byted.org/byteapi/byteapi/feishu/gateway.go`（commit 53980c9~1）的 `Send` / `makePacket` / `parseResponse`。

## 错误处理

- **HTTP 200**: 正常响应，body 是 outer Packet，inner payload 用对应 response 类型反序列化
- **HTTP 401/403**: 登录态失效（NotLoggedIn）
- **HTTP 900**: 业务错误，body 是 `errors.LarkError`（含 code/message）

## 流式答案流程

```
客户端 → cmd 1110001 PUT_AI_ROUND      (PutAIRoundRequest{query})
                                      ↓
       ← PutAIRoundResponse{ai_round, ai_topic}
客户端 → cmd 1110004 PULL_AI_ROUND_STREAMING_ANSWER  (loop, 500ms)
       ← PullAIRoundStreamingAnswerResponse {
           ai_round_status: STREAMING|FINISH|ERROR,
           oneof: { ai_answer (中间包) | ai_round (终态) }
         }
       ... 直到 status ∈ {FINISH=3, STOPPED=4, ERROR=5}
```

`AIAnswer.content` 是 `bytes`，再次反序列化为 `ai_topic_stream_search.AnswerCard`：
- `rag_answer_block.markdown` — 主答案 Markdown
- `doubao_answer_block.markdown` — 外网搜索答案
- `reference_block` — 引用列表
- `query_understanding_block.content` — Query 理解

## AIRoundStatus 枚举

| 值 | 名称 | 含义 |
|----|------|------|
| 1 | INITIAL | 已发送 query |
| 2 | STREAMING | 正在流式生成 |
| 3 | FINISH | 正常结束 |
| 4 | STOPPED | 用户中断 |
| 5 | ERROR | 异常错误 |
| 6 | PENDING | 等待用户确认 |

## 浏览器代理 fetch 模板

```javascript
async () => {
  const bytes = Uint8Array.from(atob(BASE64_BODY), c => c.charCodeAt(0));
  const r = await fetch('https://internal-api-lark-api.larksuite.com/im/gateway/', {
    method: 'POST',
    body: bytes,
    headers: {
      'content-type': 'application/x-protobuf',
      'x-request-id': crypto.randomUUID(),
    },
    credentials: 'include',
  });
  const buf = await r.arrayBuffer();
  const v = new Uint8Array(buf);
  let s = '';
  for (let i = 0; i < v.length; i++) s += String.fromCharCode(v[i]);
  return { status: r.status, body: btoa(s) };
}
```

通过 `playwright-cli eval` 注入到 ask.larksuite.com 页面执行，浏览器自动注入登录 Cookie + 任何潜在签名头。
