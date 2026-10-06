# Scene: 产品路线图 / 横向时间轴

> **建议用脚本生成**：等距分布、上下交替偏移、引导线长度都需要程序化处理，手写易导致间距不均。

## 何时用

- **产品迭代里程碑**：版本发布、关键功能上线
- **项目阶段计划**：从立项到上线的多阶段推进
- **历史大事记**：时间序列的关键事件
- **避免与甘特图混淆**：路线图突出"节点"，甘特图突出"持续时间"——多于 5 个里程碑且有起止日期改用 Mermaid gantt

## Content 约束

- **里程碑 4-8 个**（少于 4 个用列表更合适；多于 8 改纵向）
- **每个里程碑**：date（短，`2026 Q1`）+ title（产品/版本名）+ desc（一句话）
- **时间从左到右递增**

## Layout 思路

- **横向主轴**居中（黑色细横条）
- **节点圆点**等距分布，颜色独立
- **卡片上下交替**（偶数索引在上、奇数在下）
- **垂直引导线**连接圆点和卡片
- **终点黑色箭头**强化方向感

## 脚本模板

```javascript
// /tmp/wb-demo/roadmap.cjs
const { writeFileSync } = require('fs');

const titleText = "产品路线图 · Claude 模型迭代里程碑";
const subtitleText = "2024 Q1 → 2026 Q2，按季度推进。";
const milestones = [
  { date: '2024 Q1', title: 'Claude 3',           desc: '上下文 200K, 多模态' },
  { date: '2024 Q3', title: 'Claude 3.5 Sonnet',  desc: '编程能力跃迁' },
  { date: '2025 Q1', title: 'Claude 3.7',         desc: '深度推理引入' },
  { date: '2025 Q3', title: 'Claude Sonnet 4',    desc: 'Agent 工具广泛集成' },
  { date: '2026 Q1', title: 'Claude Sonnet 4.6',  desc: '长程任务稳定性' },
  { date: '2026 Q2', title: 'Claude Opus 4.7',    desc: '1M 上下文, 顶级能力' },
];

const W = 1600, H = 700;
const margin = 80;
const axisY = H / 2;
const cardW = 200, cardH = 110;
const tickR = 12;
const gap = 60;

const palette = [
  { fill: "#F0F4FC", stroke: "#5178C6" },
  { fill: "#DFF5E5", stroke: "#509863" },
  { fill: "#FEF1CE", stroke: "#D4B45B" },
  { fill: "#FEE3E2", stroke: "#D25D5A" },
  { fill: "#EAE2FE", stroke: "#8569CB" },
  { fill: "#FFF7E8", stroke: "#FF7D00" },
];

const nodes = [];
nodes.push({ type: "rect", x: 0, y: 0, width: W, height: H, fillColor: "#FFFFFF", borderWidth: 0 });
nodes.push({ type: "text", x: margin, y: 48, width: W - margin * 2, height: 36,
  text: [{ content: titleText, bold: true, fontSize: 26, color: "#1F2329" }], textAlign: "left" });
nodes.push({ type: "text", x: margin, y: 90, width: W - margin * 2, height: 24,
  text: [{ content: subtitleText, fontSize: 14, color: "#646A73" }], textAlign: "left" });

// 主轴
nodes.push({ type: "rect", x: margin, y: axisY - 2, width: W - margin * 2, height: 4,
  fillColor: "#1F2329", borderWidth: 0 });

const n = milestones.length;
const usable = W - margin * 2;
const step = usable / (n - 1);

milestones.forEach((ms, i) => {
  const cx = margin + step * i;
  const isUp = i % 2 === 0;
  const color = palette[i % palette.length];

  // 圆点
  nodes.push({ type: "ellipse", id: `tick${i}`, x: cx - tickR, y: axisY - tickR,
    width: tickR * 2, height: tickR * 2, fillColor: color.stroke, borderWidth: 0 });
  nodes.push({ type: "text", x: cx - tickR, y: axisY - tickR + 2, width: tickR * 2, height: tickR * 2,
    text: [{ content: String(i + 1), color: "#FFFFFF", bold: true, fontSize: 11 }], textAlign: "center" });

  // 卡片位置
  const cardX = cx - cardW / 2;
  const cardY = isUp ? (axisY - tickR - gap - cardH) : (axisY + tickR + gap);

  // 引导线
  nodes.push({ type: "rect", x: cx - 1,
    y: isUp ? (cardY + cardH) : (axisY + tickR),
    width: 2, height: gap, fillColor: color.stroke, borderWidth: 0 });

  // 卡片
  nodes.push({ type: "rect", x: cardX, y: cardY, width: cardW, height: cardH,
    fillColor: color.fill, strokeColor: color.stroke, borderWidth: 2, borderRadius: 10 });
  nodes.push({ type: "text", x: cardX + 14, y: cardY + 12, width: cardW - 28, height: 18,
    text: [{ content: ms.date, fontSize: 12, bold: true, color: color.stroke }], textAlign: "left" });
  nodes.push({ type: "text", x: cardX + 14, y: cardY + 34, width: cardW - 28, height: 24,
    text: [{ content: ms.title, fontSize: 16, bold: true, color: "#1F2329" }], textAlign: "left" });
  nodes.push({ type: "text", x: cardX + 14, y: cardY + 62, width: cardW - 28, height: 40,
    text: [{ content: ms.desc, fontSize: 12, color: "#646A73" }], textAlign: "left" });
});

// 终点箭头
nodes.push({ type: "ellipse", x: W - margin - 8, y: axisY - 12, width: 24, height: 24,
  fillColor: "#1F2329", borderWidth: 0,
  text: [{ content: "→", color: "#FFFFFF", bold: true, fontSize: 14 }] });

writeFileSync('/tmp/wb-demo/roadmap.json', JSON.stringify({ version: 2, nodes }, null, 2));
console.log(`roadmap.json — ${nodes.length} nodes`);
```

## 跑通

```bash
node /tmp/wb-demo/roadmap.cjs
feishu-lark call feishu_whiteboard '{"action":"draw","doc_id":"<doc_url>","input_path":"/tmp/wb-demo/roadmap.json","from":"dsl","width":1600,"height":700}'
```

## 变体

| 主题 | 怎么改 |
|---|---|
| 项目阶段（无日期）| `date` 改成 `Phase A` |
| 历史大事记 | 加大 `title` 字号、把 `date` 改成时间标签 |
| 双向时间轴 | 主轴从中间向两边延伸 |
| 带分支阶段 | 主轴外加并行分支轴 |

## 陷阱

1. **里程碑 > 8**：横向挤死，改纵向时间线
2. **日期格式不一**：`2024 Q1` 和 `2024年Q1` 混用不专业，统一空格
3. **width 必须匹配 totalWidth**：draw 传错 → 画板块截断
4. **箭头方向感**：终点用黑色圆点 + 白色 `→`，比单纯三角形稳
