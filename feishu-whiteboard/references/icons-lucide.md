# Lucide 图标集成（CLI 内置）

`feishu_whiteboard` **原生集成** [Lucide](https://lucide.dev/icons) 图标库（MIT 协议、1500+ 线条图标、统一 24×24 viewBox、stroke-width=2）。**任何信息图都该用 Lucide 替代手画图标**——视觉立刻专业一个档次。

## 两种用法

### A. `<lucide />` 占位符（推荐）

在 SVG 输入里直接写：

```xml
<svg viewBox="0 0 1800 1300" xmlns="http://www.w3.org/2000/svg">
  <!-- ... -->
  <lucide name="user"         x="106" y="171"  size="48" stroke="#8569CB"/>
  <lucide name="code"         x="106" y="358"  size="48" stroke="#5178C6"/>
  <lucide name="database"     x="106" y="514"  size="48" stroke="#509863"/>
  <lucide name="cpu"          x="106" y="824"  size="48" stroke="#D4B45B"/>
  <lucide name="circle-check" x="106" y="1138" size="48" stroke="#3C8B6B"/>
  <!-- ... -->
</svg>
```

调 `render` / `draw` / `add_nodes` 时（`from:"svg"`），工具**自动从 unpkg 取图标 + 缓存到 `/tmp/feishu-lark-wb/lucide-cache/`** + 替换为真实 SVG 片段。同名图标只会取一次。

**属性**：

| 属性 | 必填 | 说明 |
|---|---|---|
| `name` | ✅ | Lucide 图标名（小写连字符；如 `user` / `circle-check` / `arrow-right`）|
| `x` / `y` | — | 在主画布上的位置（默认 0,0）|
| `size` | — | 边长，等同 width=height（默认 24）|
| `width` / `height` | — | 分别指定时覆盖 `size` |
| `stroke` | — | 线条颜色（默认 `#1F2329`）|
| `stroke-width` | — | 线条粗细（默认 2）|
| `fill` | — | 填充（默认 `none`）|

`<lucide name="xxx"/>` 自闭合、`<lucide name="xxx"></lucide>` 双标签均支持。

### B. `action: "lucide"` 直接取（用于调研/批量）

```bash
feishu-lark call feishu_whiteboard '{
  "action": "lucide",
  "icon_names": ["user", "database", "cpu", "circle-check", "code"]
}'
```

返回：
```json
{
  "action": "lucide",
  "cache_dir": "/var/folders/.../lucide-cache",
  "icons": {
    "user":         { "svg": "<!-- @license lucide-static v1.14.0 - ISC -->\n<svg ...>...</svg>" },
    "database":     { "svg": "..." },
    "cpu":          { "svg": "..." },
    "circle-check": { "svg": "..." },
    "code":         { "svg": "..." }
  }
}
```

用途：手动查看 path / 在 DSL 脚本里读取后嵌入 `type:"svg"` 节点 / 不确定图标名时验证。

## 不知道图标叫什么？

1. 浏览 https://lucide.dev/icons 搜索关键词
2. 或先 `action: "lucide"` 试取（不存在会返回 error，可据此调整）
3. CLI 内置**legacy alias map**：`check-circle` / `x-circle` / `alert-circle` 等旧名会自动重定向到新名（v1.x 改了一些）

## 用图标增强分层泳道（实际例子）

层标签从手画图形 → Lucide 干净线条：

```xml
<!-- 之前：手画用户图标，三个原始形状拼凑 -->
<circle cx="130" cy="195" r="22" fill="#FFFFFF" stroke="#8569CB" stroke-width="2"/>
<circle cx="130" cy="186" r="7" fill="#8569CB"/>
<path d="M 113 207 Q 130 196 147 207 L 147 215 L 113 215 z" fill="#8569CB"/>

<!-- 之后：一行 Lucide 占位符 -->
<lucide name="user" x="106" y="171" size="48" stroke="#8569CB"/>
```

## 常用图标速查（按场景）

不再固化 path（lucide-static 版本会变）。只给**最常用**的名字索引，按需取：

### 用户 / 人

`user` `users` `user-check` `user-cog` `user-plus` `user-minus` `user-x`

### 代码 / 开发

`code` `code-2` `terminal` `git-branch` `git-commit` `git-pull-request` `package` `box` `archive`

### 数据 / 存储

`database` `server` `hard-drive` `cloud` `cloud-upload` `cloud-download` `file` `file-text` `folder` `inbox`

### 计算 / AI

`cpu` `brain` `sparkles` `wand-sparkles` `zap` `bot` `chip`

### 状态 / 反馈

`circle-check` `check` `circle-x` `x` `circle-alert` `circle-help` `info` `clock` `shield` `shield-check` `loader`

### 动作 / 流程

`play` `pause` `arrow-right` `arrow-left` `arrow-up` `arrow-down` `refresh-cw` `send` `download` `upload` `filter` `search` `settings` `slack` `more-horizontal`

### 图表 / 数据可视化

`bar-chart` `bar-chart-2` `line-chart` `pie-chart` `trending-up` `trending-down` `layers` `target` `gauge`

### 业务 / 商业

`shopping-cart` `dollar-sign` `credit-card` `rocket` `briefcase` `mail` `calendar` `globe`

### 装饰 / UI

`star` `heart` `flag` `eye` `lock` `unlock` `link` `external-link` `lightbulb` `bell` `bookmark` `tag`

## 配色 / 尺寸建议

| 用途 | 推荐大小 | stroke |
|---|---|---|
| 泳道左侧标签图标 | 36-48px | 对应层主色（`#8569CB` / `#5178C6` ...） |
| 章节标题前缀图标 | 24-32px | 标题文字色 |
| 步骤卡内辅助图标 | 16-20px | 卡片边框色或灰色 `#646A73` |
| 数字徽章替代 | 18-24px | 白色（用于深色 badge 背景）|

**stroke-width 调整**：放大到 36px 以上时可减到 `stroke-width="1.5"`，线条更优雅。极小（< 16px）时保持 2 反而清晰。

## 选图标的原则

1. **语义贴合**：选最直观对应的图标。配置层用 `database`，不要用 `settings`（settings 是 UI 配置面板）。
2. **统一风格**：整张图坚持用 Lucide，不要中途穿插 emoji 或 fill 实心图标。
3. **颜色 = 文字颜色或层主色**：图标 `stroke` 和该区域文字色一致。
4. **可识别度优先**：抽象图标（`cpu` / `brain`）适合泛"计算/AI"语义；具象（`shopping-cart`）适合明确业务。
5. **避免装饰过载**：每张信息图 ≤ 8 个不同图标，重复使用 OK。

## 实测信息

- 版本：lucide-static `1.14.0`（截至本文档生成时）
- 源：https://unpkg.com/lucide-static@latest/icons/<name>.svg
- 缓存：`/tmp/feishu-lark-wb/lucide-cache/<name>.svg`（首次取后无需联网）
- 协议：MIT — 可商用、可修改、无须署名

## 工具内部行为

`expandLucideTags()` 工作流程：
1. 扫描 SVG 内容里的 `<lucide ... />` 标签
2. 并发 `fetch()` 所有不重复的图标（首次走网络，后续走 `/tmp` 缓存）
3. 用真实 `<svg>...内部 paths...</svg>` 片段替换占位符
4. 写到 `/tmp/feishu-lark-wb/<uuid>.expanded.svg`，原文件不修改
5. 把 expanded 路径传给 whiteboard-cli

缓存目录不主动清理（OS 自然清理 `/tmp`）。强制重新下载：`rm /tmp/feishu-lark-wb/lucide-cache/<name>.svg`。
