# Scene: 价值金字塔（层级递减）

> **必须用脚本生成 JSON**。每层梯形的宽度按斜率系数递减，端点要精确对齐。

## 何时用

- **价值层级**：基础设施 → 核心功能 → 差异化 → 不可替代价值
- **马斯洛需求层次** 类语义：底层支撑上层，顶层最稀缺
- **数据金字塔**：data → information → knowledge → wisdom
- **避免与漏斗混淆**：金字塔强调"层级递增价值/稀缺"，漏斗强调"数量递减"——这两个朝向恰好相反

## Content 约束

- **层数 3-7**（少于 3 失去层级感；多于 7 顶层太窄）
- **每层标签**：title（短，2-4 字） + 可选 description（一句话外置）
- **建议描述外置在层右侧**：金字塔本身留干净

## Layout 思路

- **梯形递减**：底层宽 → 顶层窄，斜率 `k` 控制收窄程度（推荐 `k=0.7`）
- **冷暖色渐变**：底层冷色（蓝/灰）→ 顶层暖色（橙/红），暗示价值密度递增
- **描述外置在右侧**：每层右出一条引导线 + 文字框，避免在梯形内挤文字

## 脚本模板

```javascript
// /tmp/wb-demo/pyramid.cjs
const fs = require('fs');

const titleText = "AI 产品价值金字塔";
const subtitleText = "从底层算力到顶层不可替代差异化的层级演进";

const tiers = [
  { title: "差异化",     desc: "不可被替代的独特价值（品牌 / 数据壁垒 / 网络效应）" },
  { title: "体验",       desc: "产品打磨：交互、性能、稳定性，决定留存" },
  { title: "工程",       desc: "工程化能力：CI/CD、监控、SLA，决定可扩展" },
  { title: "模型",       desc: "选型与微调：模型能力 + Prompt 工程，决定上限" },
  { title: "基础设施",   desc: "算力 / 存储 / 数据 pipeline，决定下限" },
];

const W = 1400, H = 800;
const margin = 80;
const layerH = 90;
const slope = 0.78;  // 上下两层宽度比
const cx = 500;       // 金字塔中心 X
const baseW = 700;
const startY = H - 80 - tiers.length * layerH;

// 冷→暖色渐变
const palette = [
  { fill: "#FEE3E2", stroke: "#D25D5A" },  // 暖红（顶）
  { fill: "#FEF1CE", stroke: "#D4B45B" },  // 橙黄
  { fill: "#DFF5E5", stroke: "#509863" },  // 绿
  { fill: "#EAE2FE", stroke: "#8569CB" },  // 紫
  { fill: "#F0F4FC", stroke: "#5178C6" },  // 蓝
  { fill: "#E2E8F0", stroke: "#475569" },  // 灰（底）
];

const nodes = [];
nodes.push({ type: "rect", x: 0, y: 0, width: W, height: H, fillColor: "#FFFFFF", borderWidth: 0 });
nodes.push({ type: "text", x: margin, y: 40, width: W - margin * 2, height: 36,
  text: [{ content: titleText, bold: true, fontSize: 26, color: "#1F2329" }], textAlign: "left" });
nodes.push({ type: "text", x: margin, y: 82, width: W - margin * 2, height: 24,
  text: [{ content: subtitleText, fontSize: 14, color: "#646A73" }], textAlign: "left" });

tiers.forEach((tier, i) => {
  const color = palette[i % palette.length];
  // 从顶往下：i=0 是最顶
  const topRow = tiers.length - 1 - i;
  // 这层的底宽 = baseW * slope^topRow，顶宽 = baseW * slope^(topRow+1)
  const wBot = baseW * Math.pow(slope, topRow);
  const wTop = baseW * Math.pow(slope, topRow + 1);
  const y = startY + i * layerH;
  // 梯形 polygon：左下 → 右下 → 右上 → 左上
  // 注意 polygon 不被 DSL 直接支持；用 SVG 节点嵌入
  const points = `${cx - wBot / 2},${y + layerH} ${cx + wBot / 2},${y + layerH} ${cx + wTop / 2},${y} ${cx - wTop / 2},${y}`;
  nodes.push({
    type: "svg",
    x: cx - baseW / 2, y: startY, width: baseW, height: tiers.length * layerH,
    svg: { code: `<svg viewBox="${cx - baseW/2} ${startY} ${baseW} ${tiers.length * layerH}" xmlns="http://www.w3.org/2000/svg"><polygon points="${points}" fill="${color.fill}" stroke="${color.stroke}" stroke-width="2"/></svg>` },
  });
  // 中心 title 文字（layer 内）
  nodes.push({ type: "text", x: cx - wTop / 2, y: y + layerH / 2 - 16, width: wTop, height: 32,
    text: [{ content: tier.title, bold: true, fontSize: 18, color: color.stroke }], textAlign: "center" });

  // 描述外置（右侧）
  const descX = cx + wBot / 2 + 20;
  // 引导线
  nodes.push({ type: "connector",
    connector: { from: { x: cx + (wTop + wBot) / 4, y: y + layerH / 2 },
                 to:   { x: descX, y: y + layerH / 2 },
                 lineShape: "straight", endArrow: "none",
                 lineColor: color.stroke, strokeWidth: 1.5 } });
  // 描述文字
  nodes.push({ type: "text", x: descX + 10, y: y + layerH / 2 - 18, width: W - descX - 40, height: 16,
    text: [{ content: tier.title, bold: true, fontSize: 13, color: color.stroke }], textAlign: "left" });
  nodes.push({ type: "text", x: descX + 10, y: y + layerH / 2 + 2, width: W - descX - 40, height: 16,
    text: [{ content: tier.desc, fontSize: 12, color: "#475569" }], textAlign: "left" });
});

fs.writeFileSync('/tmp/wb-demo/pyramid.json', JSON.stringify({ version: 2, nodes }, null, 2));
console.log(`pyramid.json — ${nodes.length} nodes`);
```

## 跑通

```bash
node /tmp/wb-demo/pyramid.cjs
feishu-lark call feishu_whiteboard '{"action":"draw","doc_id":"<doc_url>","input_path":"/tmp/wb-demo/pyramid.json","from":"dsl","width":1400,"height":800}'
```

## 陷阱

1. **顶层文字太窄**：tier 多时顶层 `wTop` 收窄 → 文字被截。需保证 `wTop > 80px` 容纳 2-4 个中文字
2. **冷暖反了**：底层应该冷（基础、稳定）、顶层应该暖（稀缺、价值）；反了语义错
3. **描述塞梯形内**：层数 ≥ 4 时挤死，外置在右侧 + 引导线最稳
4. **slope 太陡**：`k < 0.5` 顶层细如针，`k > 0.85` 接近矩形不像金字塔。`0.7-0.8` 最自然
