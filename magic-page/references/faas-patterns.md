# 妙笔云函数（FaaS）模式

把 CommonJS 函数代码部署到 [`magic.solutionsuite.cn`](https://magic.solutionsuite.cn)，自动获得：

- **HTTP 端点**：`https://magic.solutionsuite.cn/api/faas/{id}` —— 调用业务 API
- **链接预览**：`https://magic.solutionsuite.cn/r?fid={id}` —— 飞书链接卡片
- **WebSocket**：`wss://magic.solutionsuite.cn/api/faas/{id}` —— 实时推送

用工具：`feishu_magic_faas`，action 只有 `publish`。

## 鉴权

同 `feishu_magic_page` —— 复用 `feishu-lark magic login` 保存的妙笔 token。

## 函数签名

```js
module.exports = async function (request, context) {
  // request: 标准 Web Request 对象 (request.url / request.headers / request.method / request.body)
  // context: { id, tenant_access_token, ... } 由妙笔运行时注入

  return new Response(JSON.stringify({ ok: true }), {
    headers: { 'Content-Type': 'application/json' },
  });
};
```

## 模式 1：HTTP API（最常用）

```js
module.exports = async function (request, context) {
  const url = new URL(request.url, 'https://magic.solutionsuite.cn');
  const name = url.searchParams.get('name') || 'world';

  return new Response(
    JSON.stringify({ greeting: `hello, ${name}!`, ts: Date.now() }),
    { headers: { 'Content-Type': 'application/json' } },
  );
};
```

发布：

```bash
feishu-lark call feishu_magic_faas '{
  "action": "publish",
  "name": "hello-api",
  "code_path": "/tmp/hello.cjs"
}'
```

返回：

```json
{
  "action": "publish",
  "mode": "create",
  "id": "vjoywgnyqlT",
  "record_id": "recvjoywgnyqlT",
  "name": "hello-api",
  "faas_url": "https://magic.solutionsuite.cn/api/faas/vjoywgnyqlT",
  "preview_url": "https://magic.solutionsuite.cn/r?fid=vjoywgnyqlT",
  "wss_url": "wss://magic.solutionsuite.cn/api/faas/vjoywgnyqlT"
}
```

调用：

```bash
curl 'https://magic.solutionsuite.cn/api/faas/vjoywgnyqlT?name=lark'
# → {"greeting":"hello, lark!","ts":1778576702103}
```

## 模式 2：飞书链接预览

返回 [`url.preview.get`](https://open.feishu.cn/document/server-docs/im-v1/url_preview/url_preview_get) 格式的 JSON，飞书会渲染成动态预览卡片：

```js
module.exports = async function (request, context) {
  return new Response(JSON.stringify({
    inline: {
      i18n_title: {
        zh_cn: '订单 #12345',
        en_us: 'Order #12345',
      },
      i18n_summary: {
        zh_cn: '客户：张三 / 金额：¥288',
        en_us: 'Customer: Zhang San / Amount: ¥288',
      },
      image_key: 'img_xxxxx',
    },
    expire_strategy: '1h',   // 缓存策略：60s / 1h / 24h / 1day
  }), { headers: { 'Content-Type': 'application/json; charset=utf-8' } });
};
```

**关键**：返回的 `preview_url` (`/r?fid={id}`) 可直接粘到飞书消息里，飞书会自动展开成卡片。若点击后要跳业务页，在消息 URL 上追加 `u=<encoded_target>`，例如 `/r?fid={id}&u=https%3A%2F%2Fkaboo.bytedance.net`。

服务端会自动识别 `expire_strategy` 并剥离，不会泄露给飞书原 API。

生产链路、实时性探针和 `v=none` 排查见 [`url-preview-sop.md`](url-preview-sop.md)。

## 模式 3：WebSocket（实时推送）

```js
module.exports = async function (request, context) {
  // 这里写 HTTP 处理；WS 走下面 ws 入口
};

// 同一文件下，导出 WS handler
module.exports.ws = async function (ws, context) {
  ws.send(JSON.stringify({ type: 'connected', id: context.id }));

  ws.on('message', (msg) => {
    // 回声
    ws.send(JSON.stringify({ echo: msg.toString() }));
  });

  ws.on('close', () => {
    console.log('[ws] closed:', context.id);
  });
};
```

连接：`wscat -c wss://magic.solutionsuite.cn/api/faas/{id}`

## 调用飞书 OpenAPI（在 FaaS 内）

FaaS 运行时注入 `context.tenant_access_token`，**无需自取**：

```js
module.exports = async function (request, context) {
  const resp = await fetch(
    'https://open.feishu.cn/open-apis/bitable/v1/apps/APP_TOKEN/tables/TABLE_ID/records',
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${context.tenant_access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ fields: { '标题': 'Hello' } }),
    },
  );
  return new Response(JSON.stringify(await resp.json()));
};
```

也可以用内置 `LarkClient`（功能更全，含分页/重试），详见原 `larkclient.md` 文档（搜索"LarkClient"）。

## 更新已有 FaaS

```bash
feishu-lark call feishu_magic_faas '{
  "action": "publish",
  "name": "hello-api",
  "id": "recvjoywgnyqlT",
  "code_path": "/tmp/hello-v2.cjs"
}'
```

URL 不变，**内容立即生效**（HTTP 调用下次请求就是新代码）。

## 代码限制

- 单段最多 95KB（服务端会自动按 95000 字符切 5 段写入多维表）
- 总长 ≤ 475KB（5 段）
- **不要**输出 / 记录任何密钥、token、cookie
- **不要**在前端泄露 `tenant_access_token`

## 安全约束

- 禁止访问 `process.env`（沙箱限制）
- 禁止读写文件系统
- 禁止 spawn 子进程
- 网络访问：只允许飞书 OpenAPI / Magic Pen Space 内网 / 公开 HTTPS

不符合的代码会发布成功但运行时报错。
