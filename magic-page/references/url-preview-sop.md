# 妙笔 FaaS 链接预览 SOP

本 SOP 沉淀飞书 `url.preview.get` + 妙笔 FaaS 的实测链路。目标是：飞书消息里展示稳定的链接预览，点击后跳到业务目标页，而不是打开 Magic HTML Box 壳子。

## 关键结论

- FaaS 返回的是预览 JSON，不要在 FaaS 里直接 `307` 跳转；跳转目标放在 `/r?fid=...&u=...` 链接参数里。
- 预览 JSON 使用飞书官方 `inline` 结构：`inline.i18n_title`、`inline.i18n_summary`、`inline.image_key`。
- `/r?fid=<fid>` 只负责触发预览；没有 `u` 时，浏览器点击会打开 `https://magic.solutionsuite.cn/html-box/vgXEWbMcsGb?fid=<fid>`。
- `/r?fid=<fid>&u=<encoded_target>` 才会在点击时跳到业务目标页，例如 Kaboo：`u=https%3A%2F%2Fkaboo.bytedance.net`。
- 飞书行内样式可能只展示标题，不展示 summary。实时性探针、版本号、关键状态要放进 `i18n_title`。
- 同一个 URL 会被飞书缓存。测试实时性时用 `v=<timestamp_or_version>` 生成新 URL；更新已发送消息要用飞书“更新 URL 预览” OpenAPI。

## 最小 FaaS 模板

```js
module.exports = async function (request, context) {
  const targetUrl = 'https://kaboo.bytedance.net';
  const imageKey = 'img_v3_xxx';
  const title = 'Kaboo';
  const summary = 'AI coding usage tracker';

  return new Response(JSON.stringify({
    inline: {
      i18n_title: {
        zh_cn: title,
        en_us: title,
      },
      i18n_summary: {
        zh_cn: summary,
        en_us: summary,
      },
      image_key: imageKey,
    },
    url: targetUrl,
    target_url: targetUrl,
    expire_strategy: '60s',
  }), {
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
    },
  });
};
```

发布后使用：

```text
https://magic.solutionsuite.cn/r?fid=<fid>&u=https%3A%2F%2Fkaboo.bytedance.net
```

`u` 必须做 URL encode。不要把长 `t2` 参数从旧链接原样塞进消息里，它可能在飞书里显示成乱码，也不负责业务跳转。

## 实时性探针模板

实时性测试要把时间和版本放在标题里，因为飞书 compact inline 预览经常不展示 summary。

```js
function pickOriginalUrl(requestUrl, payload) {
  return payload?.event?.context?.url
    || payload?.context?.url
    || payload?.url
    || payload?.original_url
    || requestUrl;
}

function pickVersion(urlText) {
  try {
    const url = new URL(urlText, 'https://magic.solutionsuite.cn');
    return url.searchParams.get('v') || 'none';
  } catch {
    return 'none';
  }
}

module.exports = async function (request, context) {
  let payload = null;
  if (request.method !== 'GET') {
    try {
      payload = await request.json();
    } catch {}
  }

  const originalUrl = pickOriginalUrl(request.url, payload);
  const version = pickVersion(originalUrl);
  const now = new Date().toLocaleTimeString('zh-CN', { hour12: false });
  const title = `Kaboo 实时 ${now} v=${version}`;

  return new Response(JSON.stringify({
    inline: {
      i18n_title: { zh_cn: title, en_us: title },
      i18n_summary: { zh_cn: '用于验证飞书链接预览缓存与 FaaS 实时执行', en_us: 'Realtime probe' },
      image_key: 'img_v3_xxx',
    },
    expire_strategy: '60s',
  }), {
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
  });
};
```

测试 URL：

```text
https://magic.solutionsuite.cn/r?fid=<fid>&v=rt-001&u=https%3A%2F%2Fkaboo.bytedance.net
```

判定方式：

| 现象 | 结论 |
|---|---|
| 改 `v` 后飞书标题立刻变 | 新 URL 已绕过缓存，FaaS 实时执行正常 |
| 同一个 `v` 等待约 60 秒后才变 | 命中飞书缓存，受 `expire_strategy` 影响 |
| 标题显示 `v=none` | FaaS 没从 `request.url` 或回调 body 的 `event.context.url` 里读到原始链接 |
| 只有标题没有摘要 | 飞书当前样式只渲染 inline title，属于预期 |

## 调试顺序

1. 先直接调 FaaS：`https://magic.solutionsuite.cn/api/faas/<fid>?v=direct-ok`，确认 JSON 和 `Content-Type` 正确。
2. 再模拟飞书 POST，把原始链接放在 `event.context.url`，确认能解析 `v`。
3. 最后把 `/r?fid=<fid>&v=<version>&u=<encoded_target>` 发进飞书，观察行内预览。
4. 点击消息里的链接，确认跳到业务目标页，而不是 `html-box/vgXEWbMcsGb`。

## 常见坑

| 坑 | 修正 |
|---|---|
| 返回 `{ title, description, inline_title }` | 改为官方 `inline.i18n_title` / `inline.i18n_summary` / `inline.image_key` |
| FaaS 直接 `307` 到业务页 | FaaS 返回 JSON，点击跳转用 `/r?...&u=<encoded_target>` |
| 点击后进了 Magic HTML Box | 链接缺少 `u` 参数 |
| 飞书里显示一坨乱码 | 不要复用长 `t2` 老链路；用新的 `/r?fid=...&u=...` |
| summary 不显示 | 把关键内容放进 `i18n_title` |
| 外部 `fetch` 失败 | 妙笔 FaaS 网络环境可能限制外部抓取；不要把它当实时反向代理，除非已用 curl 验证 |
| 已发送消息要立即刷新 | 调飞书“更新 URL 预览” OpenAPI；被动 `expire_strategy` 只影响后续拉取 |
