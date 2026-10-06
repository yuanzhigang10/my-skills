# Route: DSL JSON（脚本生成 + 调试）

DSL JSON 是 `whiteboard-cli` 的程序化输入。当 Mermaid 表达不了、SVG 又算不准坐标时，**用 Node.js .cjs 脚本生成 DSL JSON** 是最稳的方案。

## 何时用 DSL（决策树）

| 场景 | 选 DSL JSON | 选 SVG | 选 Mermaid |
|---|---|---|---|
| 流程图 / 时序图 / 类图 / ER 等标准类型 | — | — | ✅ |
| 海报 / 插画 / UI mockup / 自定义视觉 | — | ✅ | — |
| **几何复杂需要算坐标**（飞轮/鱼骨/桑基/金字塔/路线图）| ✅ | — | — |
| 大量节点 + 自动布局（dagre）| ✅ | — | — |
| 节点之间精确锚点连线 | ✅ | — | — |
| 程序化生成（数据驱动）| ✅ | — | — |

## DSL 路径 Workflow

```
1. 写 .cjs 脚本   →   /tmp/wb-demo/<name>.cjs
2. 跑生成 JSON    →   node /tmp/wb-demo/<name>.cjs  → /tmp/wb-demo/<name>.json
3. 本地预览       →   feishu_whiteboard render {input_path, from: "dsl"}
4. Read PNG 自检  →   视觉 OK 否
5. 不 OK 回到步骤 1，调脚本（不是改 JSON！）
6. OK 入飞书      →   feishu_whiteboard draw {doc_id, input_path, from: "dsl"}
```

> **永远不要手改生成出的 JSON**。改脚本，重跑——可重复、可追溯、不会引入手误。

## .cjs 脚本骨架

```javascript
// /tmp/wb-demo/<name>.cjs
const fs = require('fs');

// ═══ 1. 数据 — 唯一需要根据需求修改的部分 ═══
const data = {
  title: '主题',
  items: [
    { name: 'A', value: 100 },
    { name: 'B', value: 80 },
    // ...
  ],
};

// ═══ 2. 布局参数 ═══
const W = 1600, H = 900;
const margin = 80;
// ... 其他常量

// ═══ 3. 计算坐标 ═══
const nodes = [];
nodes.push({ type: "rect", x: 0, y: 0, width: W, height: H,
  fillColor: "#FFFFFF", borderWidth: 0 });
// 标题
nodes.push({ type: "text", x: margin, y: 40, width: W - margin * 2, height: 36,
  text: [{ content: data.title, bold: true, fontSize: 26 }], textAlign: "left" });

// 主体内容（按布局算坐标 + push nodes）
data.items.forEach((item, i) => {
  // ... 算 x, y, 上色, push 多种节点
});

// ═══ 4. 写出 ═══
fs.writeFileSync('/tmp/wb-demo/<name>.json',
  JSON.stringify({ version: 2, nodes }, null, 2));
console.log(`<name>.json — ${nodes.length} nodes, canvas ${W}x${H}`);
```

> 完整 schema 见 [`dsl-schema.md`](dsl-schema.md)，布局原语见 [`layout-patterns.md`](layout-patterns.md)。

## 调试技巧

### 1. 先压缩 / 再展开

每改一处脚本，立即重跑 render → 看 PNG → 改下一处。不要一口气改 5 处再 render，调不出来。

### 2. 调用 whiteboard-cli `--check`

```bash
npx -y @larksuite/whiteboard-cli@latest -i /tmp/wb-demo/<name>.json -f dsl --check
```

检测：
- `text-overflow`：文字溢出容器（最常见）
- `node-overlap`：节点重叠
- 直接告诉你哪个 `id` / 哪个区域有问题

### 3. 节点过多时按层 dump

把 nodes 数组按"图层"切分，依次 push + render，每加一组看一次效果：

```javascript
const layers = [
  () => pushBackground(),
  () => pushTitle(),
  () => pushAxis(),
  () => pushDataMarks(),
  () => pushLabels(),
];

// 调试时只 push 前 N 层
layers.slice(0, 3).forEach(fn => fn());
```

### 4. 用 console.log 检查坐标

脚本 push 节点时同时 log 关键坐标：

```javascript
console.log(`  [${i}] ${item.name}: x=${x.toFixed(0)} y=${y.toFixed(0)} w=${w}`);
```

发现"卡片飘到画布外"问题立刻定位。

### 5. width / height 必须等于 canvas

`draw` 时传的 `width` / `height` **必须等于脚本里的 canvas W/H**，否则画板块裁切：

```bash
# 脚本生成 canvas 1500×800
console.log(`canvas ${W}x${H}`);  # canvas 1500x800

# draw 时
'{"action":"draw","width":1500,"height":800,...}'
```

## DSL → 飞书节点 映射速记

| DSL `type` | 飞书 openapi type |
|---|---|
| `rect` / `round_rect` / `ellipse` / `diamond` / ... | `composite_shape`（不同 shape 子类型） |
| `text` | `text_shape` |
| `connector` | `connector` |
| `svg`（内嵌） | `svg`（整体降级为不可编辑图片，但渲染保真）|
| `image` | `image`（需先上传飞书素材拿 token） |
| `frame` + `layout` | `group` / `section` |

## 性能 / 规模

- 单个 JSON 最多 ~1500 节点（飞书 batch 上限）
- > 1500 节点时，工具自动分批写入（默认 1000/批，错时回退 500/250）
- 大规模数据驱动（如 500+ 行表格）建议拆成多张画板，或者直接换 Mermaid（处理大型自动布局更稳）

## 常见陷阱

1. **类型不对**：`type: "rect"`（不是 `rectangle` / `Rectangle`）；大小写敏感
2. **z-index 错乱**：nodes 数组前后即图层；先 push 的在底，后 push 的在顶
3. **`fillColor` vs `fill`**：DSL 用 `fillColor` / `strokeColor`（驼峰），不是 SVG 的 `fill` / `stroke`
4. **`text` 字段**：可以是 string 也可以是 TextRun[]（混排时用数组）
5. **connector 默认带箭头**：`endArrow` 缺省是 `arrow`，要无箭头必须显式 `"none"`
6. **lucide 不在 DSL 里**：`<lucide />` 占位符只在 SVG 路径有效；DSL 想要图标，要么用 `action: lucide` 取 path 然后嵌入 `type: "svg"` 节点

## 实战参考

完整 DSL 脚本范例见 `scenes/` 下：

- 鱼骨：[scene-fishbone.md](scenes/scene-fishbone.md)（线性插值 + 上下交替 + 同色系）
- 飞轮：[scene-flywheel.md](scenes/scene-flywheel.md)（极坐标 + 同心圆遮挡 + SVG 切割）
- 路线图：[scene-roadmap.md](scenes/scene-roadmap.md)（等距分布 + 上下交替）
- 金字塔：[scene-pyramid.md](scenes/scene-pyramid.md)（梯形递减 + 描述外置）
- 漏斗：[scene-funnel.md](scenes/scene-funnel.md)（按转化率缩放 + 流失外置）
- 组织架构：[scene-organization.md](scenes/scene-organization.md)（递归 measure-then-place）
