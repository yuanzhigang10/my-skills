---
name: magic-page
description: |
  飞书妙笔（Magic Page / HTML Box） — 在飞书云文档里嵌入可交互的 HTML 单页应用，
  或发布为独立妙笔 URL，配合云函数 FaaS / TOS 上传形成完整能力组合。

  通过 feishu-lark CLI 的 feishu_magic_doc / feishu_magic_page / feishu_magic_faas /
  feishu_tos_upload 四个工具调用。

  当以下情况时使用：
  (1) 用户要做"互动卡片"、"抽奖转盘"、"刮刮乐"、"H5 小工具"嵌入到飞书文档
  (2) 用户提到"妙笔"、"Magic Page"、"HTML Box"、"网页应用"、"小组件"、"SPA"、"互动答题"
  (3) 用户需要文档里有动态/可点击/有状态的内容（普通 markdown 表达不了）
  (4) 需要在文档里读多维表数据、调 AI、做投票、收集表单等
  (5) 需要把妙笔发布成独立 H5 链接对外分享
  (6) 需要部署 HTTP API / WebSocket / 飞书链接预览（url.preview.get）服务
  (7) 需要上传文件到 TOS 拿公开 URL（图片资源、视频等）
  (8) 需要把妙笔嵌入到外部业务系统（如 wms / 内部中台），让妙笔通过 postMessage 桥调用宿主的同源接口（每个用户独立鉴权，不写死 cookie）

  关键认知：
  - 妙笔 ≠ 普通 HTML 代码块。它由 [HTML 代码块] + [HTML Box 渲染器] 两块联合构成
  - feishu_create_doc 的 markdown 渲染器主动屏蔽 add-ons，所以**只能**用 feishu_magic_doc 嵌入
  - 妙笔运行在 sandbox iframe 里，注入 window.magic.* 和 window.bitable，禁用 localStorage
  - magic_page / magic_faas 需要妙笔 token，先跑 `feishu-lark magic login`（或 `magic login --oauth` 走飞书浏览器授权，免粘贴）
  - magic_doc 不需要妙笔 token，但仍走飞书 user/tenant token；tos_upload 小文件走匿名代理；tos multipart、magic_page publish、magic_faas publish 需要合法妙笔 token
  - bot mode 下 magic_doc 可见但默认禁用；需要配置 `botRuntime.magic.enabled=true` 后才允许 `as=bot` 创建或追加 HTML Box
---

# 飞书妙笔（Magic Page）

## 前置 · 安装 CLI

本 skill 所有工具都通过 `feishu-lark` CLI 调用。如果命令未找到，先装：

```bash
npm install -g @i18n-ecom/feishu-lark-mcp-server --registry=https://bnpm.byted.org/
```

装完用 `feishu-lark --version` 验证；首次使用妙笔（magic_page / magic_faas）前还需登录拿妙笔 token：
- `feishu-lark magic login --oauth`（推荐）：打开飞书授权页 → 授权 → 自动拿 token 存 keychain；
- `feishu-lark magic login`：去妙笔机器人输入 `dev` 复制 token 手动粘贴。

两种都存进同一个 keychain 槽，工具自动取；也可用 `MAGIC_TOKEN` 环境变量覆盖。

bot mode 注意：`feishu_magic_doc` 可以用 `as:"bot"` 走机器人/应用身份，但默认被 `botRuntime.magic.enabled=false` 拦住；显式开启后再执行。`magic_page publish` / `magic_faas publish` 仍使用妙笔 token，bot mode 下默认禁用 keychain 个人 token，优先用 `MAGIC_TOKEN`。

## 核心心智（决定输出质量）

**不要写一个孤立 HTML 文件就交差**。妙笔的真正价值是利用 `window.magic.*` 运行时调用飞书能力 —— 读多维表、取当前用户、调 AI、存共享数据。脱离这套 API 的妙笔等同于一张静态网页贴图。

正确姿态：
- **先想"为什么是妙笔"**：如果是静态展示，画板 / 图片 / markdown 表格更合适。妙笔适合**有交互、有状态、要读飞书数据**的场景
- **登录态优先用 `window.magic.currentUserInfo`**，不要走 OAuth 重新拿 token
- **存储用 `window.magic.store` / `window.magic.redis`**，**严禁** `localStorage`（sandbox iframe 跨域会失效）
- **大屏适配**：body 宽度建议 ≤ 800px（文档视窗宽度），明确 body 高度让 HTML Box 能算尺寸。**例外**：嵌入到外部业务系统全屏 iframe（见 [`embedding-in-host-page.md`](references/embedding-in-host-page.md)）时，去掉 `max-width` 限制，网格用 `repeat(auto-fill, minmax(180px, 1fr))` 自适应

---

## Workflow：从想法到嵌入文档

```
[需求] → [写 SPA HTML（遵循下文规则）] → [feishu_magic_doc 嵌入] → [飞书文档可交互]
```

### Step 1 · 设计 SPA

按下面 Rule 章节的规则写一个**单文件 HTML**（含内联 CSS/JS），用到的 API 见 [`references/api-reference.md`](references/api-reference.md)。

### Step 2 · 落盘（推荐）

```bash
cat > /tmp/magic-app.html << 'EOF'
<!DOCTYPE html>
... (你的 SPA)
EOF
```

也可以直接把 HTML 字符串作为 `html` 参数传给工具，但**大文件（>10KB）推荐落盘**避免 shell 转义出问题。

### Step 3 · 嵌入飞书文档

```bash
# 方案 A：新建文档
feishu-lark call feishu_magic_doc '{
  "action": "create",
  "title": "投票工具",
  "html_path": "/tmp/magic-app.html",
  "summary": "本文档嵌入一个团队投票小组件，所有人共享结果。"
}'

# 方案 B：追加到已有文档
feishu-lark call feishu_magic_doc '{
  "action": "add",
  "doc_id": "https://bytedance.larkoffice.com/docx/XXXXX",
  "html_path": "/tmp/magic-app.html"
}'
```

返回 `doc_url` / `code_block_id` / `html_box_block_id`，把 doc_url 给用户。

bot mode 创建：

```bash
FEISHU_BOT_MAGIC_ENABLED=true feishu-lark --auth-mode bot call feishu_magic_doc '{
  "action": "create",
  "as": "bot",
  "title": "投票工具",
  "html_path": "/tmp/magic-app.html",
  "summary": "本文档由机器人/应用身份创建并嵌入 HTML Box。"
}'
```

---

## Rule（写妙笔 HTML 的硬约束）

### 1. 存储机制

**严禁** `localStorage`（sandbox iframe 跨域）。必须用：

| 接口 | 作用域 | 用途 |
|---|---|---|
| `window.magic.store.get/set` | 当前小组件 + 当前用户 | 私有用户偏好（皮肤、上次输入） |
| `window.magic.store.global_get/global_set` | 当前小组件 + 全部用户 | 共享配置（管理员设的题目） |
| `window.magic.redis.get/set` | 当前小组件 + 当前用户 + 复制后共享 | 私有状态可跨文档复制 |
| `window.magic.redis.global_get/global_set` | 当前小组件 + 全部用户 + 复制后共享 | **投票/抽奖/留言** 等共享状态 |

```js
await window.magic.redis.global_set('vote:option_a', currentCount + 1);
const count = await window.magic.redis.global_get('vote:option_a');
```

### 2. 第三方库（CDN 白名单）

只用这三个稳定 CDN，避免 sandbox 网络限制：

- `tailwindcss` — `https://cdn.tailwindcss.com`
- `marked` — `https://cdn.jsdelivr.net/npm/marked/marked.min.js`
- `abcjs` — `https://fastly.jsdelivr.net/npm/abcjs@6.3.0/dist/abcjs-basic-min.js`

需要其他库时**先评估能不能内联实现**，不行再加 `<script src=...>`。

### 3. 环境兼容

`window.magic` / `window.lark` / `window.bitable` 在妙笔运行时存在，**本地预览时不存在**。代码里必须判断：

```js
const magic = window.magic ?? {
  // mock，便于本地预览
  currentUserInfo: { open_id: 'mock', name: '本地预览用户' },
  redis: {
    global_get: async () => 0,
    global_set: async () => ({ code: 0 }),
  },
  ai: async () => ({ code: 0, data: { result: '本地预览返回' } }),
};
```

### 4. UI/UX 约束

- **body 宽度 ≤ 800px**（文档视窗）
- **明确 body 高度**，否则 HTML Box 高度算不出来会被截
- 颜色 / 间距 / 字号要符合飞书 docx 的整体气质（淡色背景 / 圆角 / 浅阴影）

### 5. 代码风格

- `async/await` 处理异步，不要回调地狱
- 必要 try/catch 兜住网络错误
- 注释解释**为什么**，不解释**做什么**

### 6. 常见陷阱（实测踩坑）

**❌ `btoa()` 编码含 emoji / 中文的 SVG 内联图片**

```js
// 这样写会炸：InvalidCharacterError: characters outside of Latin1
const fallbackIcon = 'data:image/svg+xml;base64,' + btoa(
  '<svg ...><text>🍱</text></svg>'  // emoji 触发错误
);
```

`btoa()` 只支持 Latin1。整个 async IIFE 会因为这一行抛 unhandled rejection 而**中断后续渲染**（用户看到的现象：HTML 框架渲染了但 JS 完全没生效，用户名/选项空白）。

**✅ 正确写法**：用 `encodeURIComponent` + `charset=utf-8`

```js
const fallbackIcon = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(
  '<svg ...><text>🍱</text></svg>'
);
```

或者 SVG 里不放 emoji，纯几何图形 / ASCII。

**❌ `getCurrentUserInfo()` 返回形态当作直接 user 对象**

实测在 H5 独立访问页（非嵌入 docx）`getCurrentUserInfo()` 可能不返回 user 或返回 wrapped 对象。要**兼容多种形态**：

```js
let user = magic.currentUserInfo || magic.user;
try {
  const r = await magic.getCurrentUserInfo?.();
  user = r?.data?.user || r?.user || (r?.open_id ? r : null) || user;
} catch {}
const name = user?.name || user?.en_name || '匿名用户';
```

**❌ TOS `<img src=URL>` 加载因 `Content-Disposition: attachment` 失败的担心**

实测 TOS 公网 URL 在妙笔 sandbox iframe 内可以正常加载到 `<img>`，**不受响应头 `Content-Disposition: attachment` 影响**。可以放心引用。仅当用户**点击下载链接**时附件头才生效。

---

## 常用能力速查（详细见 references/api-reference.md）

| 场景 | API |
|---|---|
| 取当前登录用户 | `await window.magic.getCurrentUserInfo()` |
| 取文档元信息 | `await window.lark.getPageMeta()` |
| 调用 AI | `await window.magic.ai({ system, user, temperature })` |
| 读多维表 | `await window.magic.base_records_search(app_token, table_id, view_id, filter, sort, page_token, page_size)` |
| 写多维表 | `await window.magic.base_record_create(app_token, table_id, fields)` |
| 取文档评论 | `await window.magic.doc_comments_get(doc_token)` |
| 获取整篇文档 markdown | `await window.magic.getDocAsMarkdown()` |
| 多维表插件场景 | `window.bitable.*`（Base JS SDK） |
| TOS 分片上传 | `/api/tos/multipart/init` → `part` → `complete` |

---

## 最小骨架模板

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>我的妙笔</title>
  <style>
    body { margin: 0; max-width: 800px; min-height: 400px;
           font-family: -apple-system, "PingFang SC", sans-serif;
           padding: 24px; background: #F8F9FE; }
  </style>
</head>
<body>
  <div id="root">加载中…</div>
  <script>
    (async () => {
      const magic = window.magic ?? { currentUserInfo: { name: '本地用户' } };
      const user = magic.currentUserInfo || (await magic.getCurrentUserInfo?.())?.data?.user;
      document.getElementById('root').textContent = `Hi, ${user?.name ?? '匿名'}`;
    })();
  </script>
</body>
</html>
```

---

## 工具地图

四个 `feishu_magic_*` / `feishu_tos_*` 工具配合使用，覆盖妙笔完整生命周期：

| 工具 / Action | 用途 | 详细文档 |
|---|---|---|
| `feishu_magic_doc` | 把 HTML 嵌入飞书 docx 文档 | （本文档主体）|
| `feishu_magic_page` (publish) | 发布为独立妙笔 URL，可外发分享 | [`publish-to-pen-space.md`](publish-to-pen-space.md) |
| `feishu_magic_page` (extract) | 反扒已发布妙笔的源 HTML（匿名可访问的妙笔）| [`extracting-source.md`](extracting-source.md) |
| `feishu_magic_page` (list) | 列出我的/公开妙笔（`scope=mine\|public` + `title` 过滤）| [`publish-to-pen-space.md`](publish-to-pen-space.md) |
| `feishu_magic_page` (delete) | 按 `app_id` 删除妙笔 | [`publish-to-pen-space.md`](publish-to-pen-space.md) |
| `feishu_magic_faas` | 部署 CommonJS 云函数（HTTP/WSS/链接预览）| [`faas-patterns.md`](faas-patterns.md) |
| `feishu_tos_upload` | 上传文件到 TOS 拿公开 URL（大资源必经此路径，见下方上限）| [`tos-upload.md`](tos-upload.md) |

**典型组合**：
- 写 HTML → TOS 上传外部资源 → magic_page publish 拿 URL → magic_doc 嵌入文档
- 反扒别人的开源妙笔 → magic_page extract 取回源码 → 本地改造 → magic_page publish 上线
- 妙笔 HTML 调 magic_faas 部署的后端做带鉴权的接口转发

## 链接预览（FaaS 应用）

把妙笔 FaaS 当做"飞书链接预览生成器"：返回 `url.preview.get` JSON，飞书消息里粘贴 `/r?fid={id}` 即出现动态卡片。

先读 [`references/url-preview-sop.md`](references/url-preview-sop.md)：包含官方 `inline` 返回结构、`/r?fid=...&u=...` 点击跳转、实时性测试、`v=none` 排查。更多代码配方见 [`references/url-preview-recipes.md`](references/url-preview-recipes.md)。

## 嵌入到外部业务系统（postMessage 桥）

把妙笔嵌入到你自己的业务系统 iframe 里，让妙笔通过 postMessage 桥调用业务系统的**同源**接口（用当前用户的 cookie），不需要在妙笔里写死 cookie，每个用户独立鉴权。

**3 个关键事实**（不知道就建不起桥）：
1. 妙笔是**双层 iframe**（外层 Next.js 壳子 + 内层 blob iframe），所以妙笔代码必须用 `window.top.postMessage(...)` 而不是 `window.parent`
2. blob iframe 的 `event.origin` 是字符串 `'null'`（不是 null），宿主 reply 时必须过滤这个字符串降级到 `'*'`，否则浏览器抛 `Invalid target origin 'null'`
3. 单次 ping 不够，要用「主动 ping × N + 被动 hello listener + 永久 hello listener」三重保险

完整协议、代码模板、7 个常见坑、调试技巧详见 [`embedding-in-host-page.md`](embedding-in-host-page.md)。

适合替代 FaaS 写死 cookie 方案，前提是你能改业务系统前端（加 ~80 行 handler）。

## 限制与坑

- **HTML 发布上限 900,000 字符**（= 10 个 HTML 代码块 × 90,000）。`feishu_magic_page` publish 会前置拦截并报错。**超限 99% 是内联了大资源**（图片 Base64、大 JSON/CSV）——先用 `feishu_tos_upload` 上传，再在 HTML 里引用返回的 URL。`feishu_magic_doc` 嵌入同受此限。
- **文档里的 JS 必须内联进 HTML 的 `<script>`**。实测飞书 docx 的 HTML Box 会执行 html 内的 `<script>`，但**不执行** add_on record 里单独的 `js`/`scripts` 字段（官方 magic-builder 那几个隐藏字段在文档场景无效）。所以交互逻辑、外链库都写进 HTML 本身。
- **HTML Box 渲染器只读紧邻前面的代码块**。如果在代码块和 HTML Box 之间夹了其他块，渲染会丢失
- **代码块 + HTML Box 并存**是飞书 docx 的固有结构，无法只展示渲染结果。读者可看源码、可看渲染，是 feature 不是 bug
- **更新妙笔内容**：用 `feishu_update_doc` 找到 HTML 代码块替换内容；HTML Box 会自动 re-render（暂未实现 update action，下一版加）
- **画板（Mermaid/SVG）与妙笔的边界**：画板用于**静态可视化**（流程图、架构图），妙笔用于**交互**。混淆会导致选错工具
