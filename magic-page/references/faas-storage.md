# FaaS 数据存储：3 条路径（按优先级）

## 实测路径选择（基于运行时探针结论）

| 路径 | 适用 | 复杂度 |
|---|---|---|
| **① `magic.store.global_get/set`** ⭐ 推荐 | 简单 KV / 列表 / 共享状态 | 零配置，直接用 |
| **② 自建 Bitable + 加协作者** | 业务表、用户能在飞书 UI 看 | 中等（要 share 给妙笔 app）|
| **③ 外接真实后端** | 高 QPS / 事务 / SQL | 高（自己运维） |

**关键运行时事实**（从 FaaS 探针抠出来的）：

- ✅ `globalThis.magic.store.global_get/global_set` —— 妙笔自管 KV，**无需任何配置**
- ✅ `globalThis.magic.base_records_*` —— Bitable 代理，**但只能操作妙笔 app `cli_a98afe875979500d` 有权限的表**
- ✅ `process.env.LARK_APP_ID/SECRET` —— 妙笔平台官方应用凭据（注入）
- ❌ `context.tenant_access_token` —— HTTP 调用时**不存在**（仅在 /r?fid=... 链接预览入口可能注入）
- ❌ `require('redis')` / `net` / `tls` —— sandbox 禁用，**外部连接库都不能用**
- ❌ `process.env.REDIS_HOST/PORT/PASSWORD` 注入了但**没法连**（无 net 模块）

## 路径 ①：`magic.store.global_*` 当 DB（最简单）

**适合**：留言板、点赞、签到、抽奖历史、简单计数器 —— 任何能用 KV 表达的状态。

```js
module.exports = async function (request, context) {
  const store = globalThis.magic.store;

  // 读
  const list = (await store.global_get('messages:list')) || [];

  // 写（注意非事务，多 POST 同时会 race）
  list.push({ id: Math.random().toString(36).slice(2), text: '...' });
  await store.global_set('messages:list', list);

  return new Response(JSON.stringify({ count: list.length }));
};
```

**特性**：
- 跨 FaaS 实例共享（同妙笔账号下）
- 跟前端 `window.magic.store.*` **同一份数据**！前后端可以混用读写
- 值能存 JSON 序列化对象 / 数组 / number / string
- 单 key value 大小未知（实测 100 条留言对象没问题）
- **非事务**：read-modify-write 不原子。高频写场景需自己加锁或换路径 ②/③

## 路径 ②：Bitable 当 DB

**适合**：要让团队在飞书 UI 里直接看数据（CRM、订单、配置表）。

### 关键前置：把妙笔 app 加为协作者

否则 `magic.base_records_*` 调你自己建的表会报 `code=91403 Forbidden`。

```bash
# 用 UAT 调 drive permission API（CLI 当前未暴露此 action，需走 raw）
curl -X POST \
  "https://open.feishu.cn/open-apis/drive/v1/permissions/${APP_TOKEN}/members?type=bitable&need_notification=false" \
  -H "Authorization: Bearer ${UAT}" \
  -H 'Content-Type: application/json' \
  -d '{"member_type":"appid","member_id":"cli_a98afe875979500d","perm":"edit","perm_type":"container"}'
```

### 通过 `globalThis.magic.base_records_*` 操作

```js
const APP_TOKEN = 'JEwdbdBqoaeTJ7saCY2lvlgNgNd';
const TABLE_ID  = 'tblXXX';

// 列
const r = await globalThis.magic.base_records_search(APP_TOKEN, TABLE_ID, undefined, undefined, undefined, undefined, 50);
// 写
await globalThis.magic.base_record_create(APP_TOKEN, TABLE_ID, { 用户: 'A', 内容: '...' });
```

或自取 `tenant_access_token` 后直接调 `open.feishu.cn/open-apis/bitable/v1/...`（[原 SDK 路径](#sdk-完整-crud)）。

## 何时该建表 vs 复用现成的

```
用户给了 Bitable URL？
├─ 是 → 从 URL 抠 app_token + table_id，直接用
└─ 否 → 用 feishu_bitable_app create 帮用户建一张全新的
```

不要让用户自己去飞书界面手动建表 —— 我们的 CLI 工具能搞定，agent 直接做。

| 想做的事 | 方案 |
|---|---|
| 键值存储 | 一行 Bitable = 一对 key/value |
| 关系数据 | Bitable 关联字段 = 外键 |
| 跨函数共享 | 同一张 Bitable 即可 |
| 大文件 / blob | `feishu_tos_upload`（不要塞 Bitable）|
| 缓存热数据 | 链接预览 `expire_strategy: 60s/1h/24h/1day` |
| 全文检索 | ❌ 没有，filter 只支持精确匹配 |
| 事务 | ❌ 没有，Bitable 最终一致 |
| 高 QPS（>10/s） | ❌ Bitable 会限流。需重活时另搭后端 |

## 何时该建表 vs 复用现成的

```
用户给了 Bitable URL？
├─ 是 → 从 URL 抠 app_token + table_id，直接用
└─ 否 → 用 feishu_bitable_app create 帮用户建一张全新的
```

不要让用户自己去飞书界面手动建表 —— 我们的 CLI 工具能搞定，agent 直接做。

## 拿 app_token + table_id 的 4 条路径

### 路径 1：从 URL 抠（已有表）

```
https://bytedance.larkoffice.com/base/AbCdEfGhIjK?table=tblXXX&view=vewYYY
                                       ^^^^^^^^^         ^^^^^^^
                                       app_token         table_id
```

### 路径 2：列已有的 app

```bash
feishu-lark call feishu_bitable_app '{"action":"list"}'
# 拿 app_token 列表，挑一个或问用户
```

### 路径 3：列 app 下的所有 table

```bash
feishu-lark call feishu_bitable_app_table '{
  "action":"list",
  "app_token":"AbCdEfGhIjK"
}'
# 拿 table_id 列表
```

### 路径 4：建一张新的（**推荐用于 FaaS 业务专属表**）

```bash
# 第 1 步：建 app
feishu-lark call feishu_bitable_app '{
  "action":"create",
  "name":"妙笔投票数据"
}'
# → { app_token: "AbCdEfGhIjK", ... }

# 第 2 步：在 app 里建 table + 字段
feishu-lark call feishu_bitable_app_table '{
  "action":"create",
  "app_token":"AbCdEfGhIjK",
  "table_name":"votes",
  "fields":[
    {"field_name":"user_open_id", "type":1},
    {"field_name":"option",       "type":1},
    {"field_name":"voted_at",     "type":5}
  ]
}'
# → { table_id: "tblXXX", ... }
```

## 字段类型 type 速查

| `type` | 含义 | 用途示例 |
|---|---|---|
| 1 | 多行文本 | 名字、key、JSON 字符串 |
| 2 | 数字 | 计数、金额、年龄 |
| 3 | 单选 | 状态、分类 |
| 4 | 多选 | 标签 |
| 5 | 日期 | 创建时间、提交时间 |
| 7 | 复选框 | 启用/已读 |
| 11 | 人员 | 飞书用户引用（open_id 数组）|
| 13 | 电话号码 | — |
| 15 | 超链接 | 跳转 URL |
| 17 | 附件 | TOS 文件、图片 |
| 18 | 单向关联 | 关联到另一张表的记录 |
| 19 | 查找引用 | 跟随关联表的字段 |
| 20 | 公式 | 计算字段 |
| 21 | 双向关联 | 双向外键 |
| 22 | 地理位置 | — |
| 1001 | 创建时间 | 系统自动 |
| 1002 | 最后更新时间 | 系统自动 |
| 1003 | 创建人 | 系统自动 |
| 1005 | 修改人 | 系统自动 |

## SDK 完整 CRUD

下面是路径 ② Bitable 操作的底层 OpenAPI 模板（当你不想用 `globalThis.magic.base_records_*` 包装时）。

### CREATE

```js
async function insert(token, appToken, tableId, fields) {
  const resp = await fetch(
    `https://open.feishu.cn/open-apis/bitable/v1/apps/${appToken}/tables/${tableId}/records`,
    {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ fields }),
    },
  );
  const j = await resp.json();
  if (j.code !== 0) throw new Error(`insert failed: ${j.msg}`);
  return j.data.record;   // { record_id, fields }
}

// 用法
await insert(context.tenant_access_token, APP_TOKEN, TABLE_ID, {
  user_open_id: 'ou_xxx',
  option: '兰州拉面',
  voted_at: Date.now(),    // 日期字段用毫秒时间戳
});
```

### READ（带 filter）

```js
async function query(token, appToken, tableId, filter, pageSize = 100) {
  const all = [];
  let pageToken;
  while (true) {
    const resp = await fetch(
      `https://open.feishu.cn/open-apis/bitable/v1/apps/${appToken}/tables/${tableId}/records/search?page_size=${pageSize}${pageToken ? `&page_token=${pageToken}` : ''}`,
      {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ filter }),
      },
    );
    const j = await resp.json();
    if (j.code !== 0) throw new Error(`query failed: ${j.msg}`);
    all.push(...(j.data?.items ?? []));
    if (!j.data?.has_more) break;
    pageToken = j.data.page_token;
  }
  return all;
}

// 用法：找当前用户的投票
const myVotes = await query(token, APP_TOKEN, TABLE_ID, {
  conjunction: 'and',
  conditions: [
    { field_name: 'user_open_id', operator: 'is', value: ['ou_xxx'] },
  ],
});
```

### UPDATE

```js
async function update(token, appToken, tableId, recordId, fields) {
  const resp = await fetch(
    `https://open.feishu.cn/open-apis/bitable/v1/apps/${appToken}/tables/${tableId}/records/${recordId}`,
    {
      method: 'PUT',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ fields }),
    },
  );
  const j = await resp.json();
  if (j.code !== 0) throw new Error(`update failed: ${j.msg}`);
  return j.data.record;
}
```

### DELETE

```js
async function remove(token, appToken, tableId, recordId) {
  const resp = await fetch(
    `https://open.feishu.cn/open-apis/bitable/v1/apps/${appToken}/tables/${tableId}/records/${recordId}`,
    {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const j = await resp.json();
  if (j.code !== 0) throw new Error(`delete failed: ${j.msg}`);
  return true;
}
```

### 批量操作（更省 QPS）

```js
// batch_create: 一次最多 1000 条
POST /open-apis/bitable/v1/apps/{appToken}/tables/{tableId}/records/batch_create
{ "records": [{ "fields": {...} }, { "fields": {...} }, ...] }

// batch_update: 一次最多 1000 条
POST /open-apis/bitable/v1/apps/{appToken}/tables/{tableId}/records/batch_update
{ "records": [{ "record_id": "rec1", "fields": {...} }, ...] }
```

## filter 语法（关键）

```js
{
  conjunction: 'and',  // 或 'or'
  conditions: [
    {
      field_name: '字段名（注意：是显示名，不是 field_id）',
      operator: 'is',  // is / isNot / contains / doesNotContain / isEmpty /
                       // isNotEmpty / isGreater / isGreaterEqual / isLess /
                       // isLessEqual / like / in
      value: ['字符串值数组'],   // 即使单值也要数组
    },
  ],
}
```

时间字段比较：

```js
{ field_name: 'voted_at', operator: 'isGreaterEqual', value: ['ExactDate', String(Date.now() - 7*24*60*60*1000)] }
```

完整规范：https://open.larkoffice.com/document/docs/bitable-v1/app-table-record/record-filter-guide

## 常见坑

| 坑 | 解决 |
|---|---|
| filter 用 `field_id` 报错 | 用**字段显示名**（中文也行），不是 field_id |
| 日期字段 `2026-05-12` 写不进 | 用毫秒时间戳 `Date.now()` |
| 人员字段填 string 失败 | 必须 `[{ id: 'ou_xxx' }]` 数组 |
| 单选填新值报错 | 单选/多选必须是已有选项，先 update_field 加选项 |
| 写入 > 10 QPS 报限流 | 批量接口 `batch_create` 一次塞 1000 |
| filter 找不到记录 | `value` 总是数组；string operator 用 `is`/`contains`，数字用 `isGreater` |

## 推荐表结构模板

### 简单 KV 表

```js
fields: [
  { field_name: 'key',   type: 1 },   // 多行文本
  { field_name: 'value', type: 1 },   // JSON.stringify 后存
  { field_name: 'owner', type: 1 },   // 用户 open_id（实现 per-user 隔离）
  { field_name: 'ttl',   type: 5 },   // 日期，过期清理用
]
```

### 事件日志表（投票/打卡/抽奖）

```js
fields: [
  { field_name: 'user_open_id', type: 1  },
  { field_name: 'user_name',    type: 1  },
  { field_name: 'event_type',   type: 3  },   // 单选：'vote' / 'checkin' / 'spin'
  { field_name: 'payload',      type: 1  },   // JSON 字符串
  { field_name: 'created_at',   type: 1001 }, // 系统自动
]
```

### 关联表（订单 + 商品）

```js
// 商品表
fields: [{ field_name: 'name', type: 1 }, { field_name: 'price', type: 2 }]

// 订单表
fields: [
  { field_name: 'order_id',  type: 1  },
  { field_name: 'buyer',     type: 11 },   // 人员
  { field_name: 'item',      type: 18, property: { table_id: '商品表 table_id' } },  // 关联
]
```

## 跟前端 `window.magic.redis` 的关系

前端 HTML Box 的 `magic.redis.global_*` **本质就是**妙笔平台自己用 Bitable 封装的：

| 前端 | 等效 FaaS 实现 |
|---|---|
| `magic.redis.global_get('k')` | `query(...filter by key='k')` |
| `magic.redis.global_set('k', v)` | `query` 找到则 update，否则 insert |
| `magic.redis.get('k')`（私有） | 同上，filter 加 `owner=current_user` |

所以**前后端共享同一份数据的最稳姿势** = 后端 FaaS 也用同一张表。

## 与其他存储的边界

| 数据类型 | 用什么 |
|---|---|
| **结构化业务数据**（用户、订单、投票）| **Bitable** ✅ |
| **文件 / 图片 / 视频** | **TOS** (`feishu_tos_upload`) ✅ |
| **大文本（> 50KB 的 JSON）** | TOS 存 JSON 文件，Bitable 只存 URL |
| **高频计数器** | ⚠️ Bitable 限流，考虑用链接预览 `expire_strategy` 做边缘缓存兜底 |
| **二进制 blob / 嵌入向量** | TOS（Bitable 单元格只支持文本/数字） |
