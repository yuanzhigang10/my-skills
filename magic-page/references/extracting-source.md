# 反扒已发布妙笔的源 HTML（extract action）

从一个已发布的妙笔 URL 或 app_id，反扒出原始 HTML 源码（含所有内联 `<style>` / `<script>`）。

## 用途

- **改造别人的妙笔**：拿到源码 → 改业务逻辑 → 用新 app_id `publish` 上线
- **备份**：发布到妙笔后本地 HTML 文件丢了/被改坏了，从线上拉回来
- **批量审计**：脚本化遍历自己发布过的妙笔列表，dump 全部 HTML 做存档
- **学习模板**：看其他人开源的妙笔是怎么用 `window.magic.*` / `window.bitable.*` 的

## 限制

**只支持匿名可访问的妙笔**。

是否匿名可访问 ≠ `publish` 的 `is_open_source` 参数。两者无关：
- `is_open_source` 控制**妙笔空间画廊里是否展示 + 是否允许他人 remix 复用**，不影响 URL 匿名访问
- URL 是否需要登录取决于妙笔所在**工作空间 / 租户**的访问策略，由发布者所在的环境决定，不在 publish API 参数里

经验值：用 `feishu-lark magic login` 登录的 token 发布出来的妙笔（默认 my-bot profile），URL 是**匿名可访问**的。来自其他工作空间 / 租户的妙笔可能要求飞书登录（HTTP 307 → accounts.feishu.cn）。

判断匿名是否可访问的最简单方法：浏览器开**匿名/隐私窗口**贴 URL，能直接看到妙笔内容 = 匿名可访问；跳飞书登录 = 不可匿名访问，CLI extract 无法处理，见下方「替代方案」。

## 快速使用

```bash
# 用 app_id 反扒（推荐 — URL 长且容易复制错）
feishu-lark call feishu_magic_page '{
  "action": "extract",
  "app_id": "vk3Hozeb9wV",
  "output_path": "/tmp/extracted.html"
}'

# 用完整 URL 反扒（带不带 query string 都行）
feishu-lark call feishu_magic_page '{
  "action": "extract",
  "url": "https://magic.solutionsuite.cn/html-box/vk3Hozeb9wV?_=12345",
  "output_path": "/tmp/extracted.html"
}'

# 不指定 output_path：返回 JSON 里直接附带 html 字段（适合小文件 / pipeline）
feishu-lark call feishu_magic_page '{
  "action": "extract",
  "app_id": "vk3Hozeb9wV"
}' | jq -r .html > /tmp/extracted.html
```

返回示例：

```json
{
  "action": "extract",
  "source_url": "https://magic.solutionsuite.cn/html-box/vk3Hozeb9wV",
  "app_id": "vk3Hozeb9wV",
  "raw_size": 61541,
  "chunks_parsed": 7,
  "html_size": 46818,
  "output_path": "/tmp/extracted.html",
  "preview": {
    "head": "<!DOCTYPE html>\n<html lang=\"zh-CN\">\n...",
    "tail": "...</body>\n</html>"
  }
}
```

字段含义：
- `raw_size`：妙笔平台壳子 HTML 的总大小（含 Next.js 框架代码）
- `chunks_parsed`：reassemble 出多少段流式 SSR chunk —— 健康值通常 ≥ 5
- `html_size`：提取出的真实妙笔 HTML 大小（含 inline `<style>` / `<script>`）

如果传了 `output_path`，返回里**省略** `html` 字段（避免上下文/终端被 60KB 字符串刷屏），只给 `preview.head` / `preview.tail` 用于快速验证。

## 算法原理

妙笔平台的"壳子"是 Next.js（Turbopack 产物）。打开 `https://magic.solutionsuite.cn/html-box/<app_id>` 服务端先返回一个空壳 HTML，**真正的妙笔内容通过 Next.js 流式 SSR 推送**，散落在多个 `self.__next_f.push([n, "..."])` 调用里：

```html
<!-- 壳子 HTML 末尾 -->
<script>self.__next_f=self.__next_f||[]).push([0])</script>
<script>self.__next_f.push([1, "..."])</script>   <!-- 第 1 段 -->
<script>self.__next_f.push([1, "..."])</script>   <!-- 第 2 段 -->
<!-- ... -->
<script>self.__next_f.push([1, "..."])</script>   <!-- 第 N 段 -->
```

每段第二个参数是 JSON-quoted 字符串。把所有段 `JSON.parse` 后**按顺序拼接**，得到一个完整字符串，里面有真正的妙笔 HTML：

```
prefix...
<!DOCTYPE html>
<html>
...
</html>
...suffix
```

CLI 在拼接结果里切 `<!DOCTYPE` → `</html>` 段，就是源 HTML。

> 这套机制理论上可能随 Next.js / 妙笔平台升级变化。如果某天 chunks_parsed=0 或切不到 DOCTYPE，先看排查 checklist。

## 典型工作流：改造别人的开源妙笔

```bash
# 1. 反扒源码
feishu-lark call feishu_magic_page '{
  "action": "extract",
  "app_id": "vjFutO9hrJD",
  "output_path": "/tmp/origin.html"
}'

# 2. 本地改（替换 fetch URL、加桥协议、改 UI 等）
$EDITOR /tmp/origin.html

# 3. 发布到自己的 app_id 下（新 app_id —— 不传 app_id）
feishu-lark call feishu_magic_page '{
  "action": "publish",
  "html_path": "/tmp/origin.html",
  "title": "我的改造版"
}'
# → 拿到新 app_id，例如 vk3Hozeb9wV

# 4. 后续迭代复用 app_id（URL 不变）
feishu-lark call feishu_magic_page '{
  "action": "publish",
  "app_id": "vk3Hozeb9wV",
  "html_path": "/tmp/origin.html",
  "title": "我的改造版"
}'
```

## 替代方案：需要登录的妙笔源码怎么拿

CLI 的 extract 暂不支持登录态下才能访问的妙笔。当前只能手动：

1. 浏览器登录飞书后打开妙笔 URL
2. DevTools → Sources → 切到 blob iframe（双层 iframe 的内层，`origin = 'null'`）
3. 找到 HTML document，右键 `Save as` 或 Console 跑：
   ```js
   copy('<!DOCTYPE html>' + document.documentElement.outerHTML);
   ```
4. 粘到本地文件

或：DevTools Network 面板找 `/html-box/<id>` 请求，**Response** 标签里直接复制 — 然后跟匿名 case 一样跑 `self.__next_f.push` 重组算法即可。

未来如果妙笔平台有 `GET /api/html-box/<id>` 鉴权读源 API，可以让 CLI 走 magic token 鉴权读取（待考据）。

## 排查 checklist

| 现象 | 原因 | 修法 |
|---|---|---|
| `HTTP 307 → 飞书登录` | 妙笔所在工作空间/租户要求登录访问 | 见上方「替代方案」 |
| `chunks_parsed: 0` | Next.js 推送格式变了 / 目标 URL 不是妙笔 | 手动 curl + 看响应里有没有 `__next_f.push` |
| `chunks 重组成功但找不到 <!DOCTYPE`| 内容是非 HTML 妙笔（极少见） | 检查目标 URL 是否真的是 html-box |
| 提取出的 HTML `<` `>` 看起来被转义了 | 不会发生 — JSON.parse 后字符已还原 | — |
| 拉到的 HTML 比预期大很多 | 妙笔 publish 时被平台 minify/重格式化 | 正常，对比 raw_size 看是否一致即可 |

## 与 `publish` 的关系

| Action | 方向 | 鉴权 | 输入 | 输出 |
|---|---|---|---|---|
| `publish` | 本地 → 线上 | 需要 magic token | html / html_path | app_id + 4 个 URL |
| `extract` | 线上 → 本地 | **匿名** | app_id / url | html 字节流 + chunk 元信息 |

**典型组合**：`extract` 取回别人的妙笔 → 本地改造 → `publish` 上线。
