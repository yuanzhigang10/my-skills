# 通用布局原语

下列布局模式适用于**任何**可视化任务（SVG / DSL 均可）。手写坐标 → 几乎必崩；用这些公式 → 一次跑对。

## 1. 极坐标分布（飞轮 / 雷达 / 辐射）

围绕中心点等距摆放 N 个元素：

```js
const cx = 600, cy = 400, r = 280;
const startAngle = -90;  // -90 起点放在顶端；0 放右侧
for (let i = 0; i < N; i++) {
  const angle = startAngle + (i / N) * 360;
  const rad = angle * Math.PI / 180;
  const x = cx + r * Math.cos(rad);
  const y = cy + r * Math.sin(rad);
  // 放节点
}
```

**变体**：
- 不闭环（如 180° 半圆）：`(i / (N - 1)) * 180`
- 偏置中心（鸡蛋形）：`x = cx + r * 1.4 * Math.cos(rad)`
- 同心多环：多个 `r` 值，每环独立 N

## 2. 等距分布（时间轴 / 阶梯 / 进度条）

横向均匀分布 N 个里程碑：

```js
const margin = 80;
const usableWidth = totalWidth - margin * 2;
const step = usableWidth / (N - 1);
for (let i = 0; i < N; i++) {
  const x = margin + step * i;
}
```

垂直版本同理，把 `width` 换 `height`、`x` 换 `y`。

## 3. 上下交替（路线图 / 时间线）

视觉错落避免拥挤：

```js
for (let i = 0; i < N; i++) {
  const isUp = i % 2 === 0;
  const y = isUp ? (axisY - cardGap - cardHeight) : (axisY + cardGap);
}
```

## 4. 鱼骨主骨 + 斜分支

主干水平 + 上下交替分类 + 原因线性插值：

```js
const spineY = totalHeight / 2;
categories.forEach((cat, i) => {
  const isTop = i % 2 === 0;
  const spineX = margin + step * i;
  const branchDY = 180;            // 分支骨长度
  const branchDX = -branchDY * 0.7; // 斜率
  const catX = spineX + branchDX;
  const catY = isTop ? spineY - branchDY - catHeight : spineY + branchDY;

  // 沿分支骨等距挂载原因
  cat.reasons.forEach((r, j) => {
    const t = (j + 1) / (cat.reasons.length + 1);  // 线性插值
    const attachX = spineX + branchDX * t;
    const attachY = spineY + (isTop ? -branchDY : branchDY) * t;
  });
});
```

## 5. 桑基流（cubic bezier）

三列节点 + 流条 cubic-bezier 连接：

```js
// 节点矩形高度 = 流量值按比例缩放
const flowH = totalFlow * scale;

// 流条 path：(x1, y1) → 控制点 → (x2, y2)
const controlX = (x1 + x2) / 2;
const d = `M ${x1} ${y1} C ${controlX} ${y1}, ${controlX} ${y2}, ${x2} ${y2}`;
// stroke-width = flow 值，stroke-opacity = 0.4
```

## 6. 价值金字塔（梯形递减）

每层梯形宽度按斜率系数递减：

```js
const tiers = 5;
const layerHeight = 80;
const slopeFactor = 0.7;  // 上层比下层窄多少
const baseWidth = 800;
const cx = totalWidth / 2;

for (let i = 0; i < tiers; i++) {
  const w = baseWidth * Math.pow(slopeFactor, i);
  const y = totalHeight - (i + 1) * layerHeight - 100;
  // 梯形 polygon：左下 → 右下 → 右上（缩窄）→ 左上（缩窄）
  const points = [
    [cx - w/2, y + layerHeight],
    [cx + w/2, y + layerHeight],
    [cx + w*slopeFactor/2, y],
    [cx - w*slopeFactor/2, y],
  ];
}
```

## 7. 同心圆遮挡（圆环）

大圆 + 白色小圆叠加 = 圆环：

```js
// 必须按这个顺序加入 nodes
// 1. 底层大圆
{ type: "ellipse", x: cx-rOut, y: cy-rOut, width: 2*rOut, height: 2*rOut, fillColor: ringColor }
// 2. 遮罩小圆（白色）
{ type: "ellipse", x: cx-rIn, y: cy-rIn, width: 2*rIn, height: 2*rIn, fillColor: "#FFFFFF" }
// 3. 中心文字
{ type: "text", x: cx-rIn, y: cy-30, width: 2*rIn, text: [...] }
```

z-index 错乱：中心文字若在小圆之前，会被白色盖住。

## 8. SVG 切割箭头（圆环分段 + 方向感）

```js
let svg = `<svg viewBox="0 0 ${2*rOut} ${2*rOut}">`;
for (let i = 0; i < N; i++) {
  const a = -90 + i * (360 / N);
  const rad = a * Math.PI / 180;
  const da = 8;  // 折角
  const radMid = (a + da) * Math.PI / 180;
  const R1 = rIn - 5, R2 = rOut + 5, Rm = (rIn + rOut) / 2;
  const x1 = rOut + R1 * Math.cos(rad),    y1 = rOut + R1 * Math.sin(rad);
  const x2 = rOut + Rm * Math.cos(radMid), y2 = rOut + Rm * Math.sin(radMid);
  const x3 = rOut + R2 * Math.cos(rad),    y3 = rOut + R2 * Math.sin(rad);
  svg += `<polyline points="${x1},${y1} ${x2},${y2} ${x3},${y3}"
                    stroke="#FFFFFF" stroke-width="22" fill="none"
                    stroke-linejoin="round" stroke-linecap="round"/>`;
}
svg += `</svg>`;
```

## 9. 卡片极坐标偏移（避免被中心遮挡）

围绕中心放卡片时，根据角度推卡片"向外"：

```js
const tx = cx + textDist * Math.cos(rad);
const ty = cy + textDist * Math.sin(rad);
let offsetX = Math.cos(rad) > 0.1 ? 0 :
              Math.cos(rad) < -0.1 ? -boxWidth : -boxWidth / 2;
let offsetY = Math.sin(rad) > 0.1 ? 0 :
              Math.sin(rad) < -0.1 ? -boxHeight : -boxHeight / 2;
const cardX = tx + offsetX;
const cardY = ty + offsetY;
```

## 10. 网格 / 卡片墙

```js
const cols = 3;
const cardW = 280, cardH = 160;
const gap = 24;
const totalW = cols * cardW + (cols - 1) * gap;
const startX = (canvasW - totalW) / 2;

items.forEach((item, i) => {
  const row = Math.floor(i / cols);
  const col = i % cols;
  const x = startX + col * (cardW + gap);
  const y = startY + row * (cardH + gap);
});
```

## 11. 树状层级（自上而下）

```js
function layout(node, depth, x) {
  node.x = x;
  node.y = depth * (nodeH + 60);
  // 子节点居中
  const childCount = node.children.length;
  const childSpan = childCount * (nodeW + 40);
  let childX = x - childSpan / 2;
  node.children.forEach(c => {
    layout(c, depth + 1, childX);
    childX += nodeW + 40;
  });
}
```

## 12. Connector 弯折（正交折线）

避免斜直线：

```js
// 工程感强的正交连线
{ type: "connector",
  connector: { from: "a", to: "b",
    fromAnchor: "right", toAnchor: "left",
    lineShape: "orthogonal",   // 关键
    endArrow: "arrow" } }
```

## 选用建议

| 主题 | 推荐布局 |
|---|---|
| 循环 / 闭环 | 极坐标分布 + 同心圆 + SVG 切割 |
| 时间推进 | 等距分布 + 上下交替 |
| 因果分析 | 鱼骨（主骨 + 斜分支 + 线性插值）|
| 流量分流 | 桑基（cubic bezier）|
| 价值层级 | 金字塔（梯形递减）|
| 雷达 / 多维 | 极坐标多边形 + 数据多边形叠加 |
| 简单 DAG | mermaid flowchart（最省 token）|
| 自由设计 | SVG + 渐变 + 光晕 |
| 大量节点的关系网 | DSL + dagre layout |
| 网格类信息 | 网格布局 |
