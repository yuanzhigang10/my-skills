# Scene: 鱼骨图（因果分析 / 4M1E）

> **必须用脚本生成 JSON。** 鱼骨图的分支角度、原因小骨坐标需要三角函数计算，手写 JSON 必定节点重叠 / 连线穿模。

## 何时用

- **根因分析**：业务指标下滑 / 系统故障 / 质量问题溯源
- **多因素枚举**：把一个问题按 4-6 维度展开（人/机/料/法/环；或 流量/转化/商品/服务/运营）
- **避免与 mindmap 混淆**：鱼骨强调"汇聚到一个核心问题"的工程美学，mindmap 强调"向四周辐射的探索"

## Content 约束

- **分类 4-6 个**（少于 4 失去 "4M1E" 语义；多于 6 视觉拥挤）
- **每分类原因 2-4 条**（超过 4 需折叠成子鱼骨）
- **总原因 ≤ 20**（超过分类合并）

## Layout 思路

- **主骨水平**，从左向右延伸；鱼头（中心问题）在右侧，用 `ellipse` + 黑色填充
- **分类按 spineX 从左到右排列**，奇数（1、3、5）在上方，偶数（2、4）在下方
- **原因沿斜线均匀分布**（线性插值挂载）
- **主骨连线带箭头**指向鱼头，分支骨/原因小骨 `endArrow: "none"`
- **同色系**：同一分支的分类标签 / 分支骨 / 原因小骨边框 / 原因连线 **必须用同一色系**

## 脚本模板（DSL JSON 生成器）

填空 `categories` 数据即可。坐标全自动计算。

```javascript
// /tmp/wb-demo/fishbone.cjs
const fs = require('fs');
const nodes = [];

// ═══ 数据 — 唯一需要修改的部分 ═══
const titleText = "电商 GMV 下滑根因分析 · 五维鱼骨图";
const fishHead = "GMV 同比 -18%";
const categories = [
  { id: "c0", text: "流量端", reasons: ["搜索词排名下滑", "广告 ROI 衰减", "私域唤醒疲软"] },
  { id: "c1", text: "转化端", reasons: ["落地页加载缓慢", "结算流程过长", "支付失败率上升"] },
  { id: "c2", text: "商品端", reasons: ["热销品断货", "新品上架滞后", "评价管理欠缺"] },
  { id: "c3", text: "服务端", reasons: ["客服响应延迟", "退款时效不达标"] },
  { id: "c4", text: "运营端", reasons: ["营销节奏紊乱", "用户分层不细"] },
];

// ═══ 以下不需要修改 ═══
const catWidth = 140, catHeight = 44;
const reasonWidth = 160, reasonHeight = 36;
const lineLength = 24, paddingX = 48;

const branchColors = [
  { fill: "#F0F4FC", stroke: "#5178C6" },
  { fill: "#DFF5E5", stroke: "#509863" },
  { fill: "#FEF1CE", stroke: "#D4B45B" },
  { fill: "#FEE3E2", stroke: "#D25D5A" },
  { fill: "#EAE2FE", stroke: "#8569CB" },
];

let maxSpineY_up = 0, maxSpineY_down = 0;
categories.forEach((cat, index) => {
  const isTop = index % 2 === 0;
  const requiredY = (cat.reasons.length + 1) * (reasonHeight + 18);
  const branchDY = Math.max(180, requiredY);
  const branchDX = -branchDY * 0.7;
  cat.isTop = isTop; cat.branchDX = branchDX; cat.branchDY = branchDY;
  if (isTop) maxSpineY_up = Math.max(maxSpineY_up, branchDY + catHeight + 48);
  else maxSpineY_down = Math.max(maxSpineY_down, branchDY + catHeight + 48);
  cat.minX = Math.min(branchDX - catWidth / 2, branchDX - lineLength - reasonWidth);
  cat.maxX = Math.max(0, branchDX + catWidth / 2);
});

let currentSpineX = 120;
for (let i = 0; i < categories.length; i++) {
  const cat = categories[i];
  let startX = currentSpineX;
  if (i >= 2) {
    const prev = categories[i - 2];
    startX = Math.max(startX, prev.spineX + prev.maxX - cat.minX + paddingX);
  }
  if (startX + cat.minX < 60) startX = 60 - cat.minX;
  cat.spineX = startX;
  currentSpineX = startX + 90;
}

const lastCat = categories[categories.length - 1];
const spineY = maxSpineY_up + 60;
const totalWidth = lastCat.spineX + 380;
const totalHeight = spineY + maxSpineY_down + 60;

nodes.push({ type: "rect", x: 0, y: 0, width: totalWidth, height: totalHeight, fillColor: "#FFFFFF", borderWidth: 0 });
nodes.push({ type: "text", x: 40, y: 24, width: totalWidth - 80, height: 32,
  text: [{ content: titleText, bold: true, fontSize: 22 }], textAlign: "left" });

const headW = 200, headH = 88;
const headX = totalWidth - headW - 48;
const headY = spineY - headH / 2;
nodes.push({ type: "ellipse", id: "head", x: headX, y: headY, width: headW, height: headH,
  fillColor: "#1F2329", borderWidth: 0,
  text: [{ content: fishHead, color: "#FFFFFF", bold: true, fontSize: 16 }] });

const firstSpineX = categories[0].spineX + categories[0].minX - 20;
nodes.push({ type: "connector",
  connector: { from: { x: firstSpineX, y: spineY }, to: "head", toAnchor: "left",
               lineShape: "straight", endArrow: "arrow", lineColor: "#1F2329", strokeWidth: 3 } });

categories.forEach((cat, index) => {
  const color = branchColors[index % branchColors.length];
  const catX = cat.spineX + cat.branchDX - catWidth / 2;
  const catY = spineY + (cat.isTop ? -cat.branchDY - catHeight : cat.branchDY);
  nodes.push({ type: "rect", id: cat.id, x: catX, y: catY, width: catWidth, height: catHeight,
    fillColor: color.fill, strokeColor: color.stroke, borderWidth: 2, borderRadius: 8,
    text: [{ content: cat.text, bold: true, fontSize: 16, color: color.stroke }], textAlign: "center" });
  nodes.push({ type: "connector",
    connector: { from: { x: cat.spineX, y: spineY }, to: cat.id,
                 toAnchor: cat.isTop ? "bottom" : "top",
                 lineShape: "straight", endArrow: "none", lineColor: color.stroke, strokeWidth: 2 } });

  cat.reasons.forEach((reason, rIndex) => {
    const t = (rIndex + 1) / (cat.reasons.length + 1);
    const attachX = cat.spineX + cat.branchDX * t;
    const attachY = spineY + (cat.isTop ? -cat.branchDY : cat.branchDY) * t;
    const boxX = attachX - lineLength - reasonWidth;
    const boxY = attachY - reasonHeight / 2;
    const rId = `${cat.id}-r${rIndex}`;
    nodes.push({ type: "rect", id: rId, x: boxX, y: boxY, width: reasonWidth, height: reasonHeight,
      fillColor: "#FFFFFF", strokeColor: color.stroke, borderWidth: 1, borderRadius: 6,
      text: [{ content: reason, fontSize: 13, color: "#1F2329" }], textAlign: "center" });
    nodes.push({ type: "connector",
      connector: { from: { x: attachX, y: attachY }, to: rId, toAnchor: "right",
                   lineShape: "straight", endArrow: "none", lineColor: color.stroke, strokeWidth: 1.5 } });
  });
});

fs.writeFileSync('/tmp/wb-demo/fishbone.json', JSON.stringify({ version: 2, nodes }, null, 2));
console.log(`fishbone.json — ${nodes.length} nodes, canvas ${totalWidth}x${totalHeight}`);
```

## 跑通

```bash
mkdir -p /tmp/wb-demo && node /tmp/wb-demo/fishbone.cjs
feishu-lark call feishu_whiteboard '{"action":"render","input_path":"/tmp/wb-demo/fishbone.json","from":"dsl"}'
feishu-lark call feishu_whiteboard '{"action":"draw","doc_id":"<doc_url>","input_path":"/tmp/wb-demo/fishbone.json","from":"dsl","width":1516,"height":736}'
```

## 陷阱

1. **手写坐标 → 鱼骨重叠**：分支夹角、同侧水平间距、原因小骨垂直对齐必须用算法
2. **同色系混色**：错色 → 看不出分组关系；同色系 → 一眼看出"流量端"那一族都是蓝色
3. **endArrow 默认带箭头**：分支骨/原因小骨 connector 必须显式 `endArrow: "none"`
4. **鱼头不显眼**：用黑色 fill + 白色文字才能成视觉锚点
5. **width/height 传错**：`draw` 时不匹配脚本输出的 totalWidth/Height 就裁切
