# Scene: 漏斗图（转化分析）

> **必须用脚本生成 JSON**。漏斗每层宽度按转化率精确缩放，端点对齐难手算。

## 何时用

- **业务转化分析**：曝光 → 点击 → 加购 → 下单 → 支付 的多层流失
- **用户旅程衰减**：注册 → 激活 → 留存 → 付费
- **避免与金字塔混淆**：漏斗顶部最宽（最大数量）、底部最窄（最少剩下）；金字塔反过来——顶尖最窄（最稀缺价值）

## Content 约束

- **3-7 层**（少于 3 失去漏斗感；多于 7 视觉拥挤）
- **每层标签**：title + 绝对值 + 转化率（与上层相比）
- **数据必须有数值**（否则改用列表展示更合适）

## Layout 思路

- **每层等高**梯形，宽度 = 上层底宽 × 该层转化率
- **数值与转化率显示**：层内左半显示阶段名+绝对值，右半显示转化率箭头
- **流失外置**：每层右侧用红色弹出"流失 X%"标注，强化流失感
- **配色**：从顶到底色相不变、亮度递减（统一蓝色系暗度递增），暗示"漏出的人"

## 脚本模板

```javascript
// /tmp/wb-demo/funnel.cjs
const fs = require('fs');

const titleText = "下单转化漏斗 · 日活 100K 起步";
const subtitleText = "从曝光到支付的 5 层逐级转化与流失分析";

const stages = [
  { title: '曝光',     value: 100000, color: '#1E40AF' },
  { title: '点击',     value:  35000, color: '#3B82F6' },
  { title: '加购',     value:  12000, color: '#60A5FA' },
  { title: '下单',     value:   4800, color: '#93C5FD' },
  { title: '支付',     value:   3200, color: '#BFDBFE' },
];

const W = 1500, H = 800;
const margin = 80;
const layerH = 100;
const cx = 500;
const topW = 700;
const startY = 180;

const nodes = [];
nodes.push({ type: "rect", x: 0, y: 0, width: W, height: H, fillColor: "#FFFFFF", borderWidth: 0 });
nodes.push({ type: "text", x: margin, y: 40, width: W - margin * 2, height: 36,
  text: [{ content: titleText, bold: true, fontSize: 26, color: "#1F2329" }], textAlign: "left" });
nodes.push({ type: "text", x: margin, y: 82, width: W - margin * 2, height: 24,
  text: [{ content: subtitleText, fontSize: 14, color: "#646A73" }], textAlign: "left" });

const maxVal = stages[0].value;
stages.forEach((s, i) => {
  const w = topW * (s.value / maxVal);
  const wBot = i < stages.length - 1 ? topW * (stages[i + 1].value / maxVal) : w * 0.7;
  const y = startY + i * layerH;
  const points = `${cx - w / 2},${y} ${cx + w / 2},${y} ${cx + wBot / 2},${y + layerH} ${cx - wBot / 2},${y + layerH}`;

  nodes.push({
    type: "svg",
    x: cx - topW / 2, y: startY, width: topW, height: stages.length * layerH,
    svg: { code: `<svg viewBox="${cx - topW/2} ${startY} ${topW} ${stages.length * layerH}" xmlns="http://www.w3.org/2000/svg"><polygon points="${points}" fill="${s.color}" stroke="${s.color}" stroke-width="1" fill-opacity="0.92"/></svg>` },
  });

  // 阶段名
  nodes.push({ type: "text", x: cx - 200, y: y + layerH / 2 - 24, width: 180, height: 22,
    text: [{ content: s.title, bold: true, fontSize: 20, color: "#FFFFFF" }], textAlign: "right" });
  // 数值
  nodes.push({ type: "text", x: cx - 200, y: y + layerH / 2 + 4, width: 180, height: 20,
    text: [{ content: s.value.toLocaleString(), fontSize: 14, color: "#FFFFFF" }], textAlign: "right" });

  // 转化率（右侧外置）
  if (i > 0) {
    const prev = stages[i - 1].value;
    const conv = ((s.value / prev) * 100).toFixed(1);
    const lost = (((prev - s.value) / prev) * 100).toFixed(1);
    const lostCount = (prev - s.value).toLocaleString();
    const rightX = cx + topW / 2 + 40;
    nodes.push({ type: "rect", x: rightX, y: y - 8, width: 200, height: 48, rx: 8,
      fillColor: "#FEE3E2", strokeColor: "#D25D5A", borderWidth: 1, borderRadius: 8 });
    nodes.push({ type: "text", x: rightX + 12, y: y, width: 180, height: 18,
      text: [{ content: `流失 ${lost}%`, bold: true, fontSize: 14, color: "#D25D5A" }], textAlign: "left" });
    nodes.push({ type: "text", x: rightX + 12, y: y + 22, width: 180, height: 16,
      text: [{ content: `-${lostCount} 用户`, fontSize: 12, color: "#7F1D1D" }], textAlign: "left" });
    // 转化率箭头
    nodes.push({ type: "text", x: rightX, y: y + 56, width: 200, height: 18,
      text: [{ content: `↓ 转化 ${conv}%`, fontSize: 13, color: "#16A34A", bold: true }], textAlign: "left" });
  }
});

// 总转化率
const totalConv = ((stages[stages.length - 1].value / stages[0].value) * 100).toFixed(2);
nodes.push({ type: "rect", x: cx - 200, y: startY + stages.length * layerH + 24,
  width: 400, height: 60, fillColor: "#0F172A", borderWidth: 0, borderRadius: 8 });
nodes.push({ type: "text", x: cx - 200, y: startY + stages.length * layerH + 36,
  width: 400, height: 20,
  text: [{ content: "总转化率", fontSize: 13, color: "#94A3B8" }], textAlign: "center" });
nodes.push({ type: "text", x: cx - 200, y: startY + stages.length * layerH + 56,
  width: 400, height: 26,
  text: [{ content: `${totalConv}%`, bold: true, fontSize: 24, color: "#FFFFFF" }], textAlign: "center" });

fs.writeFileSync('/tmp/wb-demo/funnel.json', JSON.stringify({ version: 2, nodes }, null, 2));
console.log(`funnel.json — ${nodes.length} nodes`);
```

## 跑通

```bash
node /tmp/wb-demo/funnel.cjs
feishu-lark call feishu_whiteboard '{"action":"draw","doc_id":"<doc_url>","input_path":"/tmp/wb-demo/funnel.json","from":"dsl","width":1500,"height":800}'
```

## 陷阱

1. **底层太窄文字塞不下**：保证 `wBot > 120px`，否则减少层数或拉长 canvas
2. **数值单位不统一**：100K vs 35,000 vs 12K 混用 → 不专业。统一用 `.toLocaleString()` 或全部 K/M
3. **转化率忘记标注**：漏斗的灵魂是"流失"——必须每层右侧标 流失率 + 流失人数 + 转化率
4. **顶层数据为 0 / 负**：边界保护，避免 `maxVal = 0` 导致 NaN
5. **配色色相变化**：保持同色系（如全蓝），用透明度/亮度递减表达"漏出"
