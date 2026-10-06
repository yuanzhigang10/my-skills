# 链接预览（url.preview.get）配方

把 FaaS 函数当作"飞书链接预览生成器"使用 —— 在飞书消息里粘贴一个 `https://magic.solutionsuite.cn/r?fid={id}` 链接，飞书会自动调你的 FaaS 拉取预览 JSON，渲染成动态卡片。

## 工作流

```
1. 写 FaaS 函数（返回 url.preview.get 格式 JSON）
2. feishu_magic_faas publish → 拿 preview_url (/r?fid={id})
3. preview_url 发到飞书 → 飞书识别链接 → 显示卡片；如需点击跳业务页，追加 u=<encoded_target>
```

## 返回 JSON 字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `inline.i18n_title.zh_cn` | 必填 | 行内标题，飞书 compact 样式通常只展示这一项 |
| `inline.i18n_summary.zh_cn` | 推荐 | 摘要文本；部分飞书样式不会展示，不要放唯一关键信息 |
| `inline.image_key` | 可选 | 飞书 `img_key`（不是公开 URL） |
| `expire_strategy` | 可选 | 缓存策略：`60s` / `1h` / `24h` / `1day`（默认 `1h`） |
| `url` / `target_url` | 可选 | 业务目标 URL；点击跳转仍以 `/r?...&u=<encoded_target>` 为准 |

`expire_strategy` 是**妙笔 FaaS 平台扩展字段**，服务端会自动剥离后再传给飞书，飞书 API 看不到这个字段。

完整生产 SOP 见 [`url-preview-sop.md`](url-preview-sop.md)。不要再使用旧的 `{ title, description, inline_title, inline_image_key }` 简化结构作为新实现的主路径。

## Recipe 1：纯文本预览

```js
module.exports = async function (request, context) {
  return new Response(JSON.stringify({
    inline: {
      i18n_title: { zh_cn: '订单 #12345', en_us: 'Order #12345' },
      i18n_summary: { zh_cn: '客户：张三 / 金额：¥288 / 状态：已支付', en_us: 'Paid order' },
    },
    expire_strategy: '60s',
  }), { headers: { 'Content-Type': 'application/json; charset=utf-8' } });
};
```

发布 + 把 `preview_url` 粘到飞书消息 → 出现动态卡片。

## Recipe 2：带图标的预览（图标库匹配）

飞书图标走 `img_key`（不是公开 URL）。可以：
- **直接指定**：`inline.image_key: 'img_v3_xxx'`（你预先上传到飞书的图）
- **从图标库匹配**：调多维表查图标 `img_key`，再嵌入

简化版（直接指定 img_key）：

```js
module.exports = async function (request, context) {
  return new Response(JSON.stringify({
    inline: {
      i18n_title: { zh_cn: '部署任务 #889', en_us: 'Deploy #889' },
      i18n_summary: { zh_cn: '阶段：staging / 触发人：@王二', en_us: 'Stage: staging' },
      image_key: 'img_v3_0123_deploy_icon',
    },
    expire_strategy: '1h',
  }), { headers: { 'Content-Type': 'application/json; charset=utf-8' } });
};
```

## Recipe 3：动态数据 — 调多维表统计

```js
module.exports = async function (request, context) {
  const APP_TOKEN = 'YOUR_BITABLE_APP_TOKEN';
  const TABLE_ID = 'YOUR_TABLE_ID';

  // 调飞书 OpenAPI 查记录数
  const resp = await fetch(
    `https://open.feishu.cn/open-apis/bitable/v1/apps/${APP_TOKEN}/tables/${TABLE_ID}/records/search`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${context.tenant_access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ page_size: 1 }),
    },
  );
  const json = await resp.json();
  const total = json?.data?.total ?? 0;

  return new Response(JSON.stringify({
    inline: {
      i18n_title: { zh_cn: `Bug 总数 · ${total}`, en_us: `Bugs · ${total}` },
      i18n_summary: {
        zh_cn: `截至 ${new Date().toLocaleString('zh-CN')} / 数据源：研发 bug 看板`,
        en_us: 'Bug dashboard',
      },
    },
    expire_strategy: '24h',
  }), { headers: { 'Content-Type': 'application/json; charset=utf-8' } });
};
```

## Recipe 4：最近时间窗口统计

只统计 "最近 7 天"：

```js
module.exports = async function (request, context) {
  const APP_TOKEN = '...';
  const TABLE_ID = '...';
  const SEVEN_DAYS_MS = 7 * 24 * 60 * 60 * 1000;
  const since = Date.now() - SEVEN_DAYS_MS;

  const resp = await fetch(
    `https://open.feishu.cn/open-apis/bitable/v1/apps/${APP_TOKEN}/tables/${TABLE_ID}/records/search`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${context.tenant_access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        filter: {
          conjunction: 'and',
          conditions: [{
            field_name: '创建时间',
            operator: 'isGreaterEqual',
            value: ['ExactDate', String(since)],
          }],
        },
        page_size: 500,
      }),
    },
  );
  const json = await resp.json();
  const total = json?.data?.items?.length ?? 0;

  return new Response(JSON.stringify({
    inline: {
      i18n_title: { zh_cn: `近 7 天新增 · ${total} 条`, en_us: `Last 7 days · ${total}` },
      i18n_summary: { zh_cn: `截止 ${new Date().toLocaleString('zh-CN')}`, en_us: 'Recent window' },
    },
    expire_strategy: '1h',
  }), { headers: { 'Content-Type': 'application/json; charset=utf-8' } });
};
```

## Recipe 5：当前用户感知

`/r?fid={id}` 入口会把当前飞书用户带进 context（如可用），按用户返回不同内容：

```js
module.exports = async function (request, context) {
  const userId = context.user_id || context.open_id;
  const userName = context.user_name || '同事';

  return new Response(JSON.stringify({
    inline: {
      i18n_title: { zh_cn: `Hi ${userName}，你的待办`, en_us: `Hi ${userName}, your tasks` },
      i18n_summary: {
        zh_cn: userId ? `当前用户：${userId}` : '未识别到用户身份',
        en_us: userId ? `User: ${userId}` : 'No user identity',
      },
    },
    expire_strategy: '60s',  // 用户相关用短 TTL
  }), { headers: { 'Content-Type': 'application/json; charset=utf-8' } });
};
```

## 缓存策略选择

| `expire_strategy` | 适用场景 |
|---|---|
| `60s` | 用户相关、强时效（"我的待办数"）|
| `1h` | 一般业务数据（"Bug 总数"）|
| `24h` | 配置/字典/榜单（"本月 Top 10"）|
| `1day` | 同 24h，可读性更强（"今日打卡"）|

**不要设过短**，飞书每次展开链接都会调你的 FaaS，过短会被打爆。

## 故障排查

| 现象 | 原因 |
|---|---|
| 飞书没渲染卡片，显示纯链接 | 链接不是 `/r?fid={id}` 格式；或 FaaS 返回非 JSON / 缺 `inline.i18n_title` 字段 |
| 卡片显示"加载失败" | FaaS 报错（去 magic.solutionsuite.cn 看日志） |
| 卡片内容不更新 | 缓存未过期，等待 `expire_strategy` 时长或换 `60s` |
| 点击后打开 HTML Box | 缺少 `u=<encoded_target>` 参数 |
| 图标不显示 | `inline.image_key` 不是合法 img_key（飞书内部 key，非 URL） |

## 进阶：图标库 + 内置数据源路由

原 `magic-url-preview` skill 实现了完整的"意图识别 → 路由到内置数据源 / 图标匹配 / 自定义代码"逻辑（~600 行 FaaS 代码），可以参考：

`/Users/bytedance/projects/ai-tool/feishu-lark-cli/.superpowers/brainstorm/60914-1776870540/magic-builder/magic-url-preview/SKILL.md`

复杂场景下值得读一遍 —— 它处理了 oncall / byteworks / 多维表 / 通用代码四种路由 + 图标库相关性评分。
