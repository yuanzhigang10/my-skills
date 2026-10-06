# 嵌入外部宿主页（postMessage 桥模式）

> 把妙笔嵌入到你自己的业务系统里，让妙笔通过 postMessage 桥调用业务系统的**同源**接口（用当前用户的 cookie），不需要在妙笔里写死 cookie。

## 何时用这套方案

适合：
- 妙笔需要调用业务系统的**同源接口**（如 wms / 中后台内部接口）
- 接口有 cookie / CSRF 鉴权
- 想给「真实业务系统的用户」用，每个用户独立鉴权
- 你**有能力修改宿主业务系统的前端**（加一个 iframe 嵌入页 + 桥 handler）

**不适合**：
- 给非飞书用户用妙笔本身（妙笔强制飞书 OAuth，脱离宿主独立打开会强制登录）
- 业务系统不能改前端代码 — 没有 hook 点放 handler，这条路走不通
- 单纯展示静态内容 — 直接 markdown 表格、画板就够了

---

## 妙笔的结构（决定整套桥怎么设计）

**核心事实**：妙笔运行在一个**双层 iframe**里。

```
[你的宿主页 host.example.com]
  └─ <iframe src="https://magic.solutionsuite.cn/html-box/{app_id}">
        └─ [妙笔平台壳子 (Next.js / Turbopack)]
              └─ <iframe src="blob:https://magic.solutionsuite.cn/<uuid>">
                    └─ 你的 HTML 跑在这里（origin 字符串 = 'null'）
```

由此衍生出 7 个**必须遵守**的约束（不遵守就建不起桥）：

### 坑 1：用 `window.top` 而不是 `window.parent`

妙笔 HTML 的 `window.parent` 是中间壳子（Next.js）。给壳子发消息没人接。`window.top` 才是宿主页。

```js
// ❌ 错（发给壳子，丢失）
window.parent.postMessage(...);
// ✅ 对（直达宿主）
window.top.postMessage(...);
```

`window.top === window` 也跟着改：

```js
// ❌ 错
if (window.parent === window) { /* 独立打开 */ }
// ✅ 对
if (window.top === window) { /* 独立打开 */ }
```

### 坑 2：blob iframe 的 `event.origin` 是字符串 `'null'`，不是 `null`

HTML 规范规定 blob URL 文档的 origin 是 opaque（在 message 里序列化成字符串 `"null"`）。宿主 reply 时如果不过滤，直接当 `targetOrigin` 用会被浏览器拒绝：

```
Uncaught SyntaxError: Failed to execute 'postMessage' on 'Window':
Invalid target origin 'null' in a call to 'postMessage'.
```

宿主 reply 必须降级：

```ts
// ❌ 错（'null' 是 truthy 字符串，被当合法 origin 传出去）
src.postMessage(payload, event.origin || '*');
// ✅ 对
const safeOrigin = event.origin && event.origin !== 'null' ? event.origin : '*';
src.postMessage(payload, safeOrigin);
```

> ⚠️ 注意：这个错误**只出现在宿主侧**。妙笔发 ping 用 `'*'` 是安全的（妙笔只信任宿主回的 pong），但宿主回 pong 时如果照搬 `event.origin` 就会炸。

### 坑 3：妙笔 CDN 边缘缓存 ≤ 10s

发布后浏览器或边缘节点可能还服务旧 HTML。开发调试时**用 query 破缓存**：

```js
const iframe = document.querySelector('iframe');
iframe.src = `https://magic.solutionsuite.cn/html-box/<app_id>?_v=${Date.now()}`;
```

验证 CDN 是否已经拿到新版：

```js
fetch(`https://magic.solutionsuite.cn/html-box/<app_id>?_=${Date.now()}`)
  .then(r => r.text())
  .then(t => console.log('hit new version?', t.includes('某个新版独有的字符串')));
```

### 坑 4：握手时机 — 单次 ping 不够

妙笔加载完立刻 ping，可能赶在宿主 React `useEffect` 注册 listener 之前；妙笔平台 SDK 自身的初始化也会占用 microtask 队列，让 ping 时机更不可控。

**用三重保险**：

| 机制 | 解决的问题 |
|---|---|
| 主动 ping × N（5 次 × 600ms）| 宿主 listener 注册比妙笔晚 |
| 被动等 hello | 妙笔自己 ping 被妙笔平台 SDK 拖慢 |
| **永久 hello listener** | 即使初次 detect 失败 fallback 到 FaaS，宿主之后随时还能激活桥 |

宿主侧 iframe `onLoad` 时**主动推 hello**（覆盖纯被动等待的兜底）：

```jsx
<iframe
  onLoad={() => {
    const send = () => {
      const win = iframeRef.current?.contentWindow;
      if (!win) return;
      win.postMessage({ type: 'gswms-hello', version: '1' }, '*');
    };
    send();              // 立即
    setTimeout(send, 300);
    setTimeout(send, 1000);
    setTimeout(send, 2500);
  }}
/>
```

### 坑 5：宿主 source 校验不要太严

`event.source === iframeRef.current?.contentWindow` 严格比对在 React 重渲染 / iframe key 变化时容易短暂失配。改用更宽松的 source 非 null + path 强校验组合：

```ts
if (!event.source) return;
if (typeof msg.path !== 'string' || !msg.path.startsWith('/')) {
  reply({ type: 'gswms-api-resp', error: 'invalid path' });
  return;
}
```

`path` 必须 `/` 开头是关键安全防线 — 防止桥被借去打非业务系统域名（不然桥就是开放代理）。

### 坑 6：数据脱壳两侧要对齐

如果业务系统的 fetch 工具（如 axios 拦截器、common-fetch）**不脱业务壳**，桥拿到的是完整接口响应。FaaS 模式下你自己控的包装可能已经剥过：

```
桥拿到：       { base_resp: {...}, data: { skuList: [...] } }
FaaS 拿到：    { skuList: [...] }     // FaaS 自己剥过 wrapper
```

妙笔代码读取时统一 normalize：

```js
// 在 callViaBridge / callViaFaas 内部 normalize
function callViaBridge(...) {
  // ...
  const inner = (m.data && m.data.data) || m.data;  // 兼容
  resolve(inner);
}
```

业务代码 `resolve(inner).skuList` 单一形态，不感知模式差异。

### 坑 7：分清自己的报错和妙笔平台 SDK 的噪音

调试时 console 经常出现：

- `client handshake error : time out` （来自 `0_~-ho9tp6v6j.js`、`turbopack-*.js`）
- `Uncaught (in promise) time out` （来自 `001m3ni2r9sr3.js`）
- `refreshBasePermission`
- `WebSocket connection to 'ws://localhost:23333/' failed`

**这些都是妙笔平台自身的 SDK 噪音**（Next.js / Turbopack 产物），跟你的桥**没关系**。能区分自己代码和平台噪音是高效调试的关键。

判定方法：stack trace 里有 `vk2trm0rf0C:1` / `<app_id>:1` 的 promise 只是文件名错觉，真正出错文件是 `0_~-` / `turbopack-` 那些壳子产物。**只关心 stack 里出现你自己源码文件**（如 `index.tsx:xxx`）的报错。

---

## 协议（v1）

消息格式（双向）：

```ts
// 妙笔 → 宿主：主动握手
{ id: string, type: 'gswms-ping' }
// 宿主 → 妙笔：握手响应
{ id: string, type: 'gswms-pong', version: '1' }

// 宿主 → 妙笔：主动通知桥就绪（cover ping 未到达的兜底）
{ type: 'gswms-hello', version: '1' }

// 妙笔 → 宿主：代发同源接口请求
{
  id: string,
  type: 'gswms-api',
  path: string,                     // 必须 '/' 开头的同源路径
  method?: 'GET' | 'POST',          // 默认 POST
  body?: any,                       // JSON-serializable
  headers?: Record<string, string>,
}
// 宿主 → 妙笔：接口响应
{
  id: string,
  type: 'gswms-api-resp',
  data?: any,                       // 业务数据
  error?: string,
}
```

> 协议名可换。这里用 `gswms-*` 是历史叫法，建议项目里用 `${YOUR_PROJECT}-*` 避免冲突。

---

## 完整代码模板

### A. 宿主侧（React + 任意 fetch 工具）

```tsx
import { useEffect, useRef } from 'react';
import yourFetch from '@/utils/your-business-fetch';  // 你业务系统的同源 fetch（带 CSRF / cookie 自动处理）

const BRIDGE_VERSION = '1';

function HostPage() {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    const handler = async (event: MessageEvent) => {
      const src = event.source as Window | null;
      if (!src) return;
      const msg = event.data;
      if (!msg || typeof msg !== 'object' || typeof msg.id !== 'string') return;

      // 关键：过滤 blob iframe 的字符串 'null' origin
      const safeOrigin =
        event.origin && event.origin !== 'null' ? event.origin : '*';
      const reply = (payload: Record<string, unknown>) => {
        src.postMessage({ id: msg.id, ...payload }, safeOrigin);
      };

      if (msg.type === 'gswms-ping') {
        reply({ type: 'gswms-pong', version: BRIDGE_VERSION });
        return;
      }
      if (msg.type !== 'gswms-api') return;

      // path 必须 '/' 开头，桥只允许打同源接口
      if (typeof msg.path !== 'string' || !msg.path.startsWith('/')) {
        reply({ type: 'gswms-api-resp', error: 'invalid path' });
        return;
      }

      try {
        const data = await yourFetch(msg.path, {
          method: msg.method ?? 'POST',
          headers: { 'Content-Type': 'application/json', ...(msg.headers ?? {}) },
          body: msg.body as BodyInit,
        });
        reply({ type: 'gswms-api-resp', data });
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        reply({ type: 'gswms-api-resp', error: message });
      }
    };
    window.addEventListener('message', handler);
    return () => window.removeEventListener('message', handler);
  }, []);

  return (
    <iframe
      ref={iframeRef}
      src="https://magic.solutionsuite.cn/html-box/<app_id>"
      style={{ width: '100%', height: '100%', border: 'none' }}
      onLoad={() => {
        // iframe 加载完主动推 hello，覆盖纯被动等的时机问题
        const send = () => {
          const win = iframeRef.current?.contentWindow;
          if (!win) return;
          win.postMessage({ type: 'gswms-hello', version: BRIDGE_VERSION }, '*');
        };
        send();
        setTimeout(send, 300);
        setTimeout(send, 1000);
        setTimeout(send, 2500);
      }}
    />
  );
}
```

### B. 妙笔侧（HTML）

```js
const BRIDGE_PING_TIMEOUT = 600;
const BRIDGE_CALL_TIMEOUT = 15000;
/** @type {'detecting'|'bridge'|'faas'} */
let mode = 'detecting';

const genId = () =>
  Math.random().toString(36).slice(2) + '_' + Date.now().toString(36);

function pingOnce(timeout) {
  return new Promise((resolve) => {
    const id = genId();
    const handler = (e) => {
      if (e.data && e.data.type === 'gswms-pong' && e.data.id === id) {
        window.removeEventListener('message', handler);
        clearTimeout(timer);
        resolve(true);
      }
    };
    window.addEventListener('message', handler);
    try {
      // 双层 iframe → 必须用 window.top
      window.top.postMessage({ type: 'gswms-ping', id }, '*');
    } catch {
      window.removeEventListener('message', handler);
      resolve(false);
      return;
    }
    const timer = setTimeout(() => {
      window.removeEventListener('message', handler);
      resolve(false);
    }, timeout);
  });
}

function waitForHello(timeout) {
  return new Promise((resolve) => {
    const handler = (e) => {
      if (e.data && e.data.type === 'gswms-hello') {
        window.removeEventListener('message', handler);
        clearTimeout(timer);
        resolve(true);
      }
    };
    window.addEventListener('message', handler);
    const timer = setTimeout(() => {
      window.removeEventListener('message', handler);
      resolve(false);
    }, timeout);
  });
}

async function detectMode() {
  if (window.top === window) return 'faas';  // 独立打开 → 走 FaaS / 其他兜底
  // 双保险：active ping + passive hello race
  const active = (async () => {
    for (let i = 0; i < 5; i++) {
      if (await pingOnce(BRIDGE_PING_TIMEOUT)) return true;
    }
    return false;
  })();
  const passive = waitForHello(BRIDGE_PING_TIMEOUT * 6);
  return (await Promise.race([active, passive])) ? 'bridge' : 'faas';
}

// 关键：永久 hello listener。即使初次 detect 走了 faas，宿主之后随时还能激活桥
window.addEventListener('message', (e) => {
  if (e.data && e.data.type === 'gswms-hello' && mode !== 'bridge') {
    mode = 'bridge';
    onBridgeConnected();  // 切换 UI + 重新拉数据
  }
});

function callViaBridge(path, body) {
  return new Promise((resolve, reject) => {
    const id = genId();
    const handler = (e) => {
      const m = e.data;
      if (!m || m.type !== 'gswms-api-resp' || m.id !== id) return;
      window.removeEventListener('message', handler);
      clearTimeout(timer);
      if (m.error) reject(new Error(m.error));
      else {
        // 业务系统 fetch 不脱壳？剥一层 data 兼容
        const inner = (m.data && m.data.data) || m.data;
        resolve(inner);
      }
    };
    window.addEventListener('message', handler);
    window.top.postMessage(
      { type: 'gswms-api', id, method: 'POST', path, body },
      '*'
    );
    const timer = setTimeout(() => {
      window.removeEventListener('message', handler);
      reject(new Error('bridge timeout'));
    }, BRIDGE_CALL_TIMEOUT);
  });
}

// 启动
(async () => {
  mode = await detectMode();
  onModeDecided(mode);
  loadInitialData();
})();
```

---

## 双模式（桥 + FaaS fallback）

如果妙笔要同时支持「嵌入业务系统」和「独立打开（飞书文档 / 分享链接）」两种场景：

```js
async function callApi(path, body) {
  if (mode === 'bridge') return callViaBridge(path, body);
  return callViaFaas(path, body);  // 走预先发布的 FaaS（cookie 写死，仅 demo 用）
}
```

**关键：把两种路径的输出 normalize 到同一形态**，业务代码不感知模式差异。这通常在 `callViaBridge` / `callViaFaas` 内部完成。

---

## 自适应宽度

妙笔 SKILL.md 主体推荐 `body { max-width: 800px }`，是**文档场景**（嵌在 docx 里视窗窄）的建议。但**嵌入业务系统全屏 iframe** 时这个限制会浪费 80% 横向空间。

```css
/* 文档场景：保持 800px */
body { max-width: 800px; }
.grid { grid-template-columns: repeat(3, 1fr); }

/* 业务系统嵌入场景：自适应 */
body { /* 去掉 max-width */ }
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}
```

`auto-fill + minmax(180px, 1fr)` 让卡片网格根据 iframe 实际宽度自动选列数，文档（窄）和业务系统（宽）都好看。

---

## 调试技巧

### 1. 验证宿主 handler 注册成功

宿主页 console 装临时 listener：

```js
window.__bridgeDebug = e => {
  if (e.data?.type?.startsWith('gswms-')) {
    console.log('[bridge]', e.origin, e.data);
  }
};
window.addEventListener('message', window.__bridgeDebug);
```

然后强刷 iframe（`iframe.src += '?_v=' + Date.now()`），看是否收到妙笔的 `gswms-ping` —— 收到说明 listener 工作 + 妙笔 ping 通道 OK。

### 2. 验证层级（确认双层 iframe）

DevTools console 切到妙笔 blob frame，跑：

```js
console.log({
  parentIsTop: window.parent === window.top,  // false → 双层
  origin: location.origin,                     // magic.solutionsuite.cn
  href: location.href,                         // blob:...
});
```

### 3. 手动模拟宿主 → 妙笔 hello

在**宿主页** console（不是妙笔 frame）跑：

```js
const iframe = document.querySelector('iframe');
iframe.contentWindow.postMessage(
  { type: 'gswms-hello', version: '1' },
  '*'   // 不要传具体 origin，blob iframe 的 origin 是字符串 'null'
);
```

**banner 应立即变绿** + 妙笔自动重新加载数据。如果不变 → 妙笔代码还没拿到永久 hello listener（CDN 旧版）。

### 4. 验证 CDN 拿到新版

```js
fetch(`https://magic.solutionsuite.cn/html-box/<app_id>?_=${Date.now()}`)
  .then(r => r.text())
  .then(t => console.log('contains new sentinel:', t.includes('某段新版独有的字符串')));
```

---

## 排查 checklist

| 现象 | 最可能原因 | 修法 |
|---|---|---|
| 妙笔一直 FaaS 兜底，console 没有桥相关报错 | 妙笔用了 `window.parent`，应是 `window.top` | 改 |
| 宿主 listener 收到 ping 但妙笔不切桥 | reply targetOrigin 是字符串 `'null'` | 过滤后降级 `'*'` |
| 妙笔报 `Invalid target origin 'null'`（stack 指向你自己的代码）| 同上 | 同上 |
| 桥连上了但业务数据为 0 / undefined | 两种模式数据脱壳层级不一致 | callViaBridge / FaaS 内部 normalize |
| Console 大量 `client handshake error : time out` | 妙笔平台 SDK 自身噪音 | 忽略 |
| 改完代码不生效 | 妙笔 CDN 边缘缓存 / dev server 未重启 | URL 加 `?_v=Date.now()`；重启 dev server |
| 嵌进业务系统右侧大量留白 | body `max-width: 800px` 文档场景默认 | 去掉，用 auto-fill 网格 |
| 手动 `iframe.contentWindow.postMessage(...)` 推 hello 无效 | 妙笔代码 hello listener 是 one-shot（detectMode 结束就 remove）| 改成永久 listener |
| 拼了 query 想破缓存但 magic 报 `replaceState failed` | query 被改成 hash 注入 blob URL，无害报错 | 忽略 |

---

## 与现有方案对比

| 方案 | 适用 | cookie | 用户体验 |
|---|---|---|---|
| **桥模式**（本文档）| 嵌入到自己的业务系统，给真实用户用 | 用户自己的，每人独立 | 无感 |
| **FaaS 写死 cookie**（见 [`faas-patterns.md`](./faas-patterns.md)）| demo / 自测 / 极少数人内部 | 单一用户写死，公开等同泄露 | 不需要登录 |
| **业务接口加 CORS** | 业务团队配合 | 用户自己的 | 但要后端发版 + 长期维护白名单 |
| **业务同源放代理页 + iframe 嵌妙笔** | 类似桥模式但反向 | 用户自己的 | 业务前端要放专用代理 HTML |

桥模式对前端最友好：**只在宿主前端加 ~80 行 handler + iframe onLoad 推 hello，妙笔加双模式判断**，不动后端、不动接口、不开 CORS。
