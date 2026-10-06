# DSL JSON Schema

`@larksuite/whiteboard-cli` 接受 DSL JSON 作为 `-f dsl` 的输入。本文档完整定义 schema 与节点类型，让你能写出**任意结构**的画板，而不是固定几张图。

## 顶层结构

```json
{
  "version": 2,
  "nodes": [ ... ]
}
```

`version` 固定 `2`。`nodes` 是节点数组，**顺序即 z-index**（先入数组的在下层，后入的覆盖在上）。

## 节点公共字段

```ts
{
  type: NodeType,
  id?: string,                   // 用于 connector 引用；不填自动生成
  x: number,                     // 左上角坐标
  y: number,
  width: number,
  height: number,
  fillColor?: string,            // 填充色 (#RRGGBB)
  strokeColor?: string,          // 描边色
  borderColor?: string,          // 兼容别名 = strokeColor
  borderWidth?: number,          // 默认 1；0 = 无边
  borderRadius?: number,         // 圆角半径
  text?: TextRun[] | string,     // 节点内文字；详见下方 TextRun
  textAlign?: "left" | "center" | "right",
  rotation?: number,             // 旋转角度（度）
}
```

## NodeType 枚举

| type | 用途 | 必填特有字段 |
|---|---|---|
| `rect` | 矩形（最常用，做卡片/背景/分区）| — |
| `ellipse` | 椭圆 / 圆形（圆点、鱼头）| — |
| `text` | 纯文字（无背景）| `text` 必填 |
| `connector` | 连线 / 箭头 | `connector` 对象 |
| `svg` | 内嵌 SVG 片段 | `svg.code` |
| `image` | 图片 | `image.token`（飞书素材 token）|
| `frame` | 容器（带 layout） | `layout` |

> ⚠️ **不支持的飞书画板专属类型**（在 DSL 里写了会被忽略或降级）：
> `sticky_note` / `mind_map` / `table_uml` / `life_line` / `combined_fragment` — 它们只在 `openapi` 输出中作为 OpenAPI 节点类型存在，不能从 DSL 直接生成。

## TextRun（富文本）

`text` 字段可以是：

```ts
type Text = string | TextRun[];

interface TextRun {
  content: string,
  bold?: boolean,
  italic?: boolean,
  fontSize?: number,             // 默认 14
  color?: string,                // 文字颜色
  backgroundColor?: string,
}
```

混排示例（标题 + 副标题同一行）：
```json
"text": [
  { "content": "获取", "bold": true, "fontSize": 18, "color": "#5178C6" },
  { "content": "  Acquisition", "fontSize": 12, "color": "#646A73" }
]
```

## connector 详解

```ts
{
  type: "connector",
  connector: {
    from: { x: number, y: number } | string,       // 起点：绝对坐标 或 节点 id
    to:   { x: number, y: number } | string,       // 终点：同上
    fromAnchor?: "top"|"right"|"bottom"|"left"|"center",
    toAnchor?:   "top"|"right"|"bottom"|"left"|"center",
    lineShape?: "straight" | "curved" | "orthogonal",  // 默认 curved
    startArrow?: "none" | "arrow" | "triangle",
    endArrow?:   "none" | "arrow" | "triangle",        // 默认 arrow
    lineColor?: string,
    strokeWidth?: number,
    lineStyle?: "solid" | "dash" | "dot",
  }
}
```

**`from`/`to` 用法**：
- 绝对坐标 `{x, y}`：画板上固定一点（用于"主骨连线"等无锚点起点）
- 节点 id 字符串：自动吸附到节点边缘；需配合 `fromAnchor`/`toAnchor` 控制方位

**两种典型组合**：

| 用途 | from | to | endArrow |
|---|---|---|---|
| 流程图主向 | 节点 id | 节点 id | `arrow` |
| 鱼骨主骨 → 鱼头 | `{x,y}` 主骨左端点 | `head` id | `arrow` |
| 鱼骨分支骨 / 原因小骨 | `{x,y}` 主骨某点 | 分类 id | **`"none"`** |
| 引导线（非箭头）| 节点 id | 节点 id | `"none"` |

## frame（容器 + layout）

```ts
{
  type: "frame",
  layout: "vertical" | "horizontal" | "grid" | "none",
  gap?: number,
  padding?: number,
  alignItems?: "start" | "center" | "end" | "stretch",
  borderWidth?: number,
  borderRadius?: number,
  fillColor?: string,
  width: number | "fit-content",         // 注意 layout: "none" 时必须固定数字
  height: number | "fit-content",
  children: Node[],                       // 嵌套
}
```

**布局规则**：
- `layout: "vertical"` / `"horizontal"` / `"grid"`：子节点 `x`/`y` 被忽略，由 layout 计算
- `layout: "none"`：子节点用绝对 `x`/`y`，**容器 width/height 必须固定数字**（不能 `fit-content`）
- 嵌套 frame 默认作为不透明子节点参与父布局

> **避坑**：`layout: "none"` + `width: "fit-content"` 会导致内部绝对定位的节点超出容器边界，全部错位。务必固定数字。

## svg 节点（内嵌 SVG 片段）

```ts
{
  type: "svg",
  x, y, width, height,
  svg: { code: "<svg viewBox='...'>...</svg>" }
}
```

用于自由几何（圆环切割箭头、装饰路径等）。**svg 节点本身在画板里不可编辑**——会作为整体降级为内嵌图片。

## 节点顺序 = z-index

`nodes` 数组前→后 = 底层→顶层。常见错误：

| ❌ 错 | ✅ 对 |
|---|---|
| 中心文字 → 外层圆 | 外层圆 → 中心文字（否则被盖）|
| 卡片 → 切割 SVG | 切割 SVG → 卡片 |
| 箭头 → 端点节点 | 端点节点 → 箭头（箭头要压在节点之上）|

## 完整最小示例

```json
{
  "version": 2,
  "nodes": [
    { "type": "rect", "x": 0, "y": 0, "width": 800, "height": 400, "fillColor": "#FFFFFF", "borderWidth": 0 },

    { "type": "rect", "id": "a", "x": 80, "y": 160, "width": 160, "height": 80,
      "fillColor": "#F0F4FC", "strokeColor": "#5178C6", "borderWidth": 2, "borderRadius": 8,
      "text": [{ "content": "起点", "bold": true, "fontSize": 16, "color": "#5178C6" }],
      "textAlign": "center" },

    { "type": "rect", "id": "b", "x": 560, "y": 160, "width": 160, "height": 80,
      "fillColor": "#DFF5E5", "strokeColor": "#509863", "borderWidth": 2, "borderRadius": 8,
      "text": [{ "content": "终点", "bold": true, "fontSize": 16, "color": "#509863" }],
      "textAlign": "center" },

    { "type": "connector",
      "connector": { "from": "a", "to": "b", "fromAnchor": "right", "toAnchor": "left",
                     "lineShape": "straight", "endArrow": "arrow",
                     "lineColor": "#1F2329", "strokeWidth": 2 } }
  ]
}
```

存为 `/tmp/wb-demo/minimal.json` →`feishu-lark call feishu_whiteboard '{"action":"render","input_path":"/tmp/wb-demo/minimal.json","from":"dsl"}'`

## 用脚本生成（推荐）

任何需要**坐标算式**（极坐标、等距分布、三角函数、布局对齐）的图表 → 写 .cjs 脚本输出 JSON：

```javascript
// /tmp/wb-demo/<name>.cjs
const fs = require('fs');
const nodes = [];
// ... 算坐标、push 节点 ...
fs.writeFileSync('/tmp/wb-demo/<name>.json', JSON.stringify({ version: 2, nodes }, null, 2));
```

跑：`node /tmp/wb-demo/<name>.cjs` → `feishu_whiteboard render/draw input_path:/tmp/wb-demo/<name>.json`

具体设计模式（极坐标布局、对称结构、层级递减、交替分布）见 [`layout-patterns.md`](layout-patterns.md)。
