# Scene: 增长飞轮（Growth Flywheel）

> **必须用脚本生成 JSON。** 飞轮需要极坐标计算阶段卡片位置 + SVG 圆环切割 + 同心圆遮挡，手写 JSON 无法正确实现圆环结构。

## 何时用

- **自驱循环模型**：增长闭环（AARRR / 海盗指标）、产品价值循环、运营飞轮
- **多阶段相互推动**：每阶段提升加速下阶段，强调"正反馈"语义
- **避免与 mindmap / 辐射图混淆**：飞轮强调"顺时针推进"的方向感，需要箭头切割

## Content 约束

- **阶段 3-6 个**（默认 4 个；超过 6 圆环碎片化）
- **每阶段**：短 title（中文 2-4 字）+ 可选 subtitle（英文）+ 可选 desc 一句话
- **中心**：主题标题（≤ 6 字）+ 可选副标题

## Layout 思路

1. **同心圆遮挡法**：大圆（深色填充）+ 小圆（白色覆盖）= 圆环
2. **SVG 切割箭头**：圆环上叠白色粗线 polyline 形成分段 + 顺时针方向感
3. **阶段卡片**：极坐标 `(cx + r·cosθ, cy + r·sinθ)` 均匀分布
4. **z-index 严格**：底层大圆 → 遮罩小圆 → 中心文字 → SVG 切割 → 外围卡片

## 脚本模板

```javascript
// /tmp/wb-demo/flywheel.cjs
const { writeFileSync } = require('fs');

const centerTitle = '增长飞轮';
const centerSubtitle = 'Claude × 飞书';
const titleText = '增长飞轮 · Growth Flywheel';
const subtitleText = '四阶段自驱闭环：每一阶段的提升加速下一阶段。';
const stages = [
  { title: '获取', subtitle: 'Acquisition', desc: '通过开放工具与社区驱动新用户进入' },
  { title: '激活', subtitle: 'Activation', desc: '首次价值时刻 < 5 分钟，零摩擦上手' },
  { title: '留存', subtitle: 'Retention', desc: '高频任务自动化，每日打开次数 6+' },
  { title: '推荐', subtitle: 'Referral', desc: '共享 skill 与文档形成网络效应' },
];

const N = stages.length;
const cx = 600, cy = 460;
const rOut = 240, rIn = 160;
const textDist = rOut + 50;
const boxW = 240, boxH = 96;
const da = 8;
const W = 1200, H = 920;
const ringColor = "#5178C6";
const stageColors = [
  { fill: "#F0F4FC", stroke: "#5178C6" },
  { fill: "#DFF5E5", stroke: "#509863" },
  { fill: "#FEF1CE", stroke: "#D4B45B" },
  { fill: "#FEE3E2", stroke: "#D25D5A" },
  { fill: "#EAE2FE", stroke: "#8569CB" },
  { fill: "#FFF7E8", stroke: "#FF7D00" },
];

const nodes = [];
nodes.push({ type: "rect", x: 0, y: 0, width: W, height: H, fillColor: "#FFFFFF", borderWidth: 0 });

// 标题
nodes.push({ type: "text", x: 80, y: 36, width: W - 160, height: 32,
  text: [{ content: titleText, bold: true, fontSize: 24, color: "#1F2329" }], textAlign: "left" });
nodes.push({ type: "text", x: 80, y: 74, width: W - 160, height: 24,
  text: [{ content: subtitleText, fontSize: 14, color: "#646A73" }], textAlign: "left" });

// 图层 1: 底层大圆
nodes.push({ type: "ellipse", x: cx - rOut, y: cy - rOut, width: rOut * 2, height: rOut * 2,
  fillColor: ringColor, borderWidth: 0 });

// 图层 2: 遮罩小圆
nodes.push({ type: "ellipse", x: cx - rIn, y: cy - rIn, width: rIn * 2, height: rIn * 2,
  fillColor: "#FFFFFF", borderWidth: 0 });

// 图层 3: 中心文字
nodes.push({ type: "text", x: cx - rIn, y: cy - 30, width: rIn * 2, height: 36,
  text: [{ content: centerTitle, bold: true, fontSize: 30, color: "#1F2329" }], textAlign: "center" });
if (centerSubtitle) {
  nodes.push({ type: "text", x: cx - rIn, y: cy + 18, width: rIn * 2, height: 24,
    text: [{ content: centerSubtitle, fontSize: 16, color: "#646A73" }], textAlign: "center" });
}

// 图层 4: SVG 切割箭头
let svg = `<svg viewBox="0 0 ${rOut * 2} ${rOut * 2}" xmlns="http://www.w3.org/2000/svg">`;
for (let i = 0; i < N; i++) {
  const a = -90 + i * (360 / N);
  const rad = (a * Math.PI) / 180;
  const radMid = ((a + da) * Math.PI) / 180;
  const R1 = rIn - 5, R2 = rOut + 5, Rm = (rIn + rOut) / 2;
  const x1 = rOut + R1 * Math.cos(rad), y1 = rOut + R1 * Math.sin(rad);
  const x2 = rOut + Rm * Math.cos(radMid), y2 = rOut + Rm * Math.sin(radMid);
  const x3 = rOut + R2 * Math.cos(rad), y3 = rOut + R2 * Math.sin(rad);
  svg += `<polyline points="${x1},${y1} ${x2},${y2} ${x3},${y3}" stroke="#FFFFFF" stroke-width="22" fill="none" stroke-linejoin="round" stroke-linecap="round"/>`;
}
svg += `</svg>`;
nodes.push({ type: "svg", x: cx - rOut, y: cy - rOut, width: rOut * 2, height: rOut * 2, svg: { code: svg } });

// 图层 5: 外围阶段卡片
for (let i = 0; i < N; i++) {
  const stage = stages[i];
  const color = stageColors[i % stageColors.length];
  const a = -90 + (360 / N) / 2 + i * (360 / N);
  const rad = (a * Math.PI) / 180;
  const tx = cx + textDist * Math.cos(rad);
  const ty = cy + textDist * Math.sin(rad);
  let offsetX = Math.cos(rad) > 0.1 ? 0 : (Math.cos(rad) < -0.1 ? -boxW : -boxW / 2);
  let offsetY = Math.sin(rad) > 0.1 ? 0 : (Math.sin(rad) < -0.1 ? -boxH : -boxH / 2);
  const cardX = tx + offsetX, cardY = ty + offsetY;

  nodes.push({ type: "rect", x: cardX, y: cardY, width: boxW, height: boxH,
    fillColor: color.fill, strokeColor: color.stroke, borderWidth: 2, borderRadius: 10 });
  nodes.push({ type: "ellipse", x: cardX + 12, y: cardY + 12, width: 24, height: 24,
    fillColor: color.stroke, borderWidth: 0,
    text: [{ content: String(i + 1), color: "#FFFFFF", bold: true, fontSize: 14 }] });
  nodes.push({ type: "text", x: cardX + 44, y: cardY + 10, width: boxW - 56, height: 24,
    text: [
      { content: stage.title, bold: true, fontSize: 18, color: color.stroke },
      { content: "  " + (stage.subtitle ?? ""), fontSize: 12, color: "#646A73" },
    ], textAlign: "left" });
  if (stage.desc) {
    nodes.push({ type: "text", x: cardX + 16, y: cardY + 44, width: boxW - 32, height: 40,
      text: [{ content: stage.desc, fontSize: 12, color: "#1F2329" }], textAlign: "left" });
  }
}

writeFileSync('/tmp/wb-demo/flywheel.json', JSON.stringify({ version: 2, nodes }, null, 2));
console.log(`flywheel.json — ${nodes.length} nodes`);
```

## 跑通

```bash
node /tmp/wb-demo/flywheel.cjs
feishu-lark call feishu_whiteboard '{"action":"render","input_path":"/tmp/wb-demo/flywheel.json","from":"dsl"}'
feishu-lark call feishu_whiteboard '{"action":"draw","doc_id":"<doc_url>","input_path":"/tmp/wb-demo/flywheel.json","from":"dsl","width":1200,"height":920}'
```

## 陷阱

1. **z-index 错乱**：中心文字必须在大圆和小圆之后；SVG 切割必须在中心文字之后
2. **缺方向感**：SVG polyline 必须带 `da` 折角偏转，否则就是普通环形分段
3. **stages > 6**：圆环每段太小，文字撑不开。拆主图
4. **stages < 3**：圆环分段太大，留白难看。改用横向流程图
5. **极坐标偏移没算对**：卡片在 0°/180°/90°/270° 时需手动调 offset
