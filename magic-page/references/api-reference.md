# 妙笔 API 参考

详细罗列 HTML Box 运行时注入的全部能力。SKILL.md 的"常用能力速查"是入口，本文是字典。

## 运行时说明

- **HTML Box**（嵌入 docx 的妙笔块）：直接可用 `window.magic.*` / `window.lark.*`
- **FaaS**（妙笔云函数）：同样注入 `window.magic` / `window.lark`，并提供全局别名 `magic` / `lark`
- **本地预览**：上述全局都**不存在**，必须 mock（见 SKILL.md 的"环境兼容"）
- **多维表插件**：另外注入 `window.bitable`，等效于 `import { bitable } from '@lark-base-open/js-sdk'`，详见 https://lark-base-team.github.io/js-sdk-docs/

## 当前用户信息

```js
// 同步读缓存
const cached = window.magic.currentUserInfo;
const cachedUser = window.magic.user;

// 异步刷新（推荐用这个）
const user = await window.magic.getCurrentUserInfo();
// 兼容旧版：
const user2 = await window.magic.getCurrentUser();
```

结构：

```json
{
  "open_id": "ou_xxx",
  "name": "用户名",
  "en_name": "English Name",
  "avatar_url": "https://..."
}
```

`getCurrentUserInfo()` 通过父页面登录态请求，并回写 `currentUserInfo` / `user`。

**兼容写法**（旧代码用 fetch 直接打）：

```js
const resp = await fetch('/api/me');
const json = await resp.json();
```

sandbox iframe 里 `/api/me` 被运行时**代理到父页面**执行（携带登录 cookie）。未登录返回 401。**前端不要保存 user access token** —— 调用飞书用户态接口走服务端 FaaS。

## 按 open_id 取用户信息

```js
await window.magic.getUserInfoById('ou_7dab8a3d3cdcc9da365777c7ad535d62');
```

返回：

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "user": {
      "open_id": "ou_7dab8a3d3cdcc9da365777c7ad535d62",
      "name": "张三",
      "en_name": "San Zhang",
      "nickname": "Alex Zhang",
      "avatar": {
        "avatar_72": "https://...",
        "avatar_240": "https://...",
        "avatar_640": "https://...",
        "avatar_origin": "https://..."
      }
    }
  }
}
```

## 文档基本信息

```js
const meta = await window.lark.getPageMeta();
```

返回示例：

```json
{
  "doc_token": "doccnfYZzTlvXqZIGTdAHKabcef",
  "title": "sampletitle",
  "owner_id": "ou_b13d41c02edc52ce66aaae67bf1abcef",
  "owner_user": { "open_id": "ou_xxx", "cn_name": "名字", "avatar_url": "https://..." },
  "url": "https://sample.feishu.cn/docs/doccnfYZzTlvXqZIGTdAHKabcef",
  "create_timestamp": 1673426766,
  "create_time": "1652066345",
  "latest_modify_user": "ou_b13d...",
  "latest_modify_time": "1652066345",
  "pv": 1,
  "uv": 1,
  "comments_count": 0,
  "sec_label_name": "L2-内部"
}
```

## 文档评论

```js
const result = await window.magic.doc_comments_get(doc_token);
```

返回 `data.items[]`，每项含 `comment_id`、`user_id`、`quote`、`reply_list` 等。

## 整篇文档 markdown

```js
const md = await window.magic.getDocAsMarkdown();
```

适合做"文档摘要"、"文档转脑图"等场景。

## 存储（替代 localStorage）

> **严禁 `localStorage`**。sandbox iframe 跨域会失效。

|  | 私有数据（用户独享） | 共有数据（用户共享） | 权限要求 |
|---|---|---|---|
| **当前小组件独享** | `magic.store.get/set` | `magic.store.global_get/global_set` | 阅读权限 |
| **复制后仍共享** | `magic.redis.get/set` | `magic.redis.global_get/global_set` | 编辑权限 |

- **私有**：当前用户独自可见，他人无感知
- **共有**：所有访客共享，即时同步
- "有哪些人参与"类逻辑 → 用 `global_*` 接口

```js
// 私有偏好
await window.magic.store.set('theme', 'dark');
const theme = await window.magic.store.get('theme');

// 共享投票
await window.magic.redis.global_set('vote:a', 42);
const count = await window.magic.redis.global_get('vote:a');
```

## AI 调用

```js
await window.magic.ai({
  system: 'You are a poet.',
  user: '写一首关于春天的诗',
  temperature: 0.7,
  thinking: { type: 'disabled' },          // 或 'enabled' 开启深度思考
  reasoning_effort: 'minimal',             // 'minimal' | 'medium' | 'high'
});
// → { code: 0, data: { result: 'AI 返回的文本' } }
```

## 多维表 — 读

```js
await window.magic.base_records_search(
  app_token,
  table_id,
  view_id,        // 可选
  filter,         // 条件，详见下文
  sort,           // [{ field_name, desc }]
  page_token,     // 第一页传 undefined
  page_size,      // 100 / 500
);
```

`filter` 规范：https://open.larkoffice.com/document/docs/bitable-v1/app-table-record/record-filter-guide

请求示例：

```js
await window.magic.base_records_search(
  'HaVFwEUN8iUUyVk4v6Nc7dbenOf',
  'tblYlY0M6sngLJjc',
  'vewaIuHxPl',
  {
    conjunction: 'and',
    conditions: [
      { field_name: '字段1', operator: 'is', value: ['文本内容'] },
    ],
  },
  [{ desc: true, field_name: '多行文本' }],
);
```

返回：

```json
{
  "code": 0,
  "data": {
    "has_more": false,
    "items": [{
      "fields": {
        "数字字段": 96,
        "文本字段": [{ "text": "内容", "type": "text" }]
      }
    }],
    "page_token": "",
    "total": 1
  }
}
```

**全量拉取的标准姿势**：

```js
async function fetchAllBaseRecords(appToken, tableId, viewId, filter, sort) {
  const all = [];
  let pageToken;
  while (true) {
    const resp = await window.magic.base_records_search(
      appToken, tableId, viewId, filter, sort, pageToken, 500,
    );
    if (resp.code !== 0) throw new Error(resp.msg || 'base_records_search failed');
    all.push(...(resp.data.items ?? []));
    if (!resp.data.has_more) break;
    pageToken = resp.data.page_token;
  }
  return all;
}
```

## 多维表 — 按 record_id 批量取

```js
await window.magic.base_records_get(app_token, table_id, record_ids);
```

返回：

```json
{
  "code": 0,
  "data": {
    "absent_record_ids": [],
    "forbidden_record_ids": [],
    "records": [{
      "fields": { "字段名": "字段值" },
      "record_id": "recv5IqcPLqCR7"
    }]
  }
}
```

## 多维表 — 写

```js
await window.magic.base_record_create(app_token, table_id, fields);
```

示例（抽奖中奖记录）：

```js
await window.magic.base_record_create(
  'MUPpbjdeRaOcF1sa1FkcqT1Tnpg',
  'tbl0OMllgriuo6Pt',
  {
    '中奖人':   [{ id: 'open_id' }],   // 人员字段：id 数组
    '奖品':     '充电宝',
    '收件人':   '阿毛',
    '联系电话': '12345678910',
    '邮寄地址': '北京市海淀区xxx',
  },
);
```

## TOS 分片上传

绕过 16MB 请求体限制。流程：

### 1) 初始化

```http
POST /api/tos/multipart/init
{ "filename": "video.mp4", "contentType": "video/mp4" }
```

返回 `uploadId` / `key` / `url`。

### 2) 上传分片

```http
POST /api/tos/multipart/part
Content-Type: multipart/form-data
fields: file (Blob) / uploadId / key / partNumber (从 1 起)
```

返回 `{ partNumber, etag }`。

### 3) 合并分片

```http
POST /api/tos/multipart/complete
{
  "uploadId": "xxx",
  "key": "uploads/1700000000000_video.mp4",
  "parts": [
    { "partNumber": 1, "etag": "\"9b2cf535...\"" },
    { "partNumber": 2, "etag": "\"0a6e4a1b...\"" }
  ]
}
```

### 4) 终止（可选）

```http
POST /api/tos/multipart/abort
{ "uploadId": "xxx", "key": "uploads/..." }
```

### 前端范例

```js
async function uploadMultipart(file, partSize = 10 * 1024 * 1024) {
  // 1) init
  const initResp = await fetch('/api/tos/multipart/init', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename: file.name, contentType: file.type }),
  });
  const { data: { uploadId, key } } = await initResp.json();
  const parts = [];

  // 2) parts
  let partNumber = 1;
  for (let start = 0; start < file.size; start += partSize, partNumber++) {
    const fd = new FormData();
    fd.append('file', file.slice(start, start + partSize));
    fd.append('uploadId', uploadId);
    fd.append('key', key);
    fd.append('partNumber', String(partNumber));
    const partResp = await fetch('/api/tos/multipart/part', { method: 'POST', body: fd });
    const partJson = await partResp.json();
    parts.push({ partNumber, etag: partJson.data.etag });
  }

  // 3) complete
  const completeResp = await fetch('/api/tos/multipart/complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ uploadId, key, parts }),
  });
  return (await completeResp.json()).data.url;
}
```

**注意**：
- `partNumber` 从 1 开始递增，**不允许跳号**
- `parts` 必须含全部分片 `etag`，否则 complete 失败
- 单片建议 5–10MB；最大 16MB（请求体限制）

## 多维表插件 SDK（window.bitable）

仅在**多维表格插件场景**（侧边栏、应用模式）才注入。HTML Box 嵌入 docx 时**不可用**。

```js
const bitable = window.bitable;
const table = await bitable.base.getActiveTable();
const records = await table.getRecords({ pageSize: 100 });
```

完整文档：https://lark-base-team.github.io/js-sdk-docs/

---

## 调试技巧

- **本地预览**：直接 `open file:///path/to/app.html`，配合 mock 的 `window.magic`
- **看 HTML Box 报错**：飞书 docx 内右键检查 → Console（iframe 通常被沙箱化，需用 DevTools 选对 frame）
- **共享状态查不到**：检查是不是用了 `redis.global_*` 而非 `redis.*`
- **登录态丢失**：刷新文档；如果 `/api/me` 持续 401，让用户重新登录飞书 web
