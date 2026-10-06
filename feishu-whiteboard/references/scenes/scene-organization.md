# Scene: 组织架构图（树形层级）

> **结构简单可手写 DSL**，节点超过 20 个建议用 mermaid `flowchart TD` 或脚本递归生成。

## 何时用

- **公司组织架构**：CEO → VP → 总监 → 经理 → 员工
- **决策链 / 汇报关系**：明确的上下级树状结构
- **产品线 / 业务单元**：按部门或产品线拆分
- **避免与 mind map 混淆**：组织架构强调严格的"父子上下级"，mind map 强调"中心辐射"

## Content 约束

- **层级 3-5**（过深可读性差，可折叠子节点）
- **每节点**：name + role + 可选 avatar 占位
- **同级节点 ≤ 8**（多于 8 需要二级分组或滚动）

## Layout 思路

- **方向**：`flowchart TD`（top-down）最自然；横向时用 `LR`
- **节点形状**：高级用圆角矩形，普通员工用纯矩形
- **颜色编码**：按部门一色或按层级一色
- **连接线**：直角折线（orthogonal），避免斜线

## 方案 A：Mermaid（最快）

```bash
cat > /tmp/wb-demo/org.mmd <<'EOF'
flowchart TD
  CEO["CEO<br/>张三"]:::lvl1
  CTO["CTO<br/>李四"]:::lvl2
  CPO["CPO<br/>王五"]:::lvl2
  CFO["CFO<br/>赵六"]:::lvl2

  CEO --> CTO
  CEO --> CPO
  CEO --> CFO

  ENG_VP["工程 VP"]:::lvl3
  INFRA["基础设施"]:::lvl4
  WEB["前端"]:::lvl4
  PROD_VP["产品 VP"]:::lvl3
  DESIGN["设计"]:::lvl4
  RESEARCH["用户研究"]:::lvl4

  CTO --> ENG_VP
  ENG_VP --> INFRA
  ENG_VP --> WEB
  CPO --> PROD_VP
  PROD_VP --> DESIGN
  PROD_VP --> RESEARCH

  classDef lvl1 fill:#1F2329,stroke:#1F2329,color:#FFFFFF
  classDef lvl2 fill:#EAE2FE,stroke:#8569CB,color:#1F2329
  classDef lvl3 fill:#F0F4FC,stroke:#5178C6,color:#1F2329
  classDef lvl4 fill:#FFFFFF,stroke:#5178C6,color:#1F2329
EOF

feishu-lark call feishu_whiteboard '{
  "action":"draw","doc_id":"<doc_url>",
  "input_path":"/tmp/wb-demo/org.mmd","from":"mermaid"
}'
```

## 方案 B：DSL 脚本（控制更细 / 节点带 avatar 占位 / 大型组织）

```javascript
// /tmp/wb-demo/org.cjs
const fs = require('fs');

const titleText = "公司组织架构 · 2026 Q2";

// 树形数据
const tree = {
  id: 'ceo', name: 'CEO 张三', role: '集团 CEO', color: '#0F172A', textColor: '#FFFFFF',
  children: [
    { id: 'cto', name: 'CTO 李四', role: '技术负责人', color: '#EAE2FE', stroke: '#8569CB',
      children: [
        { id: 'eng-vp', name: '工程 VP', role: '王某', color: '#F0F4FC', stroke: '#5178C6',
          children: [
            { id: 'web', name: '前端团队', role: '12 人', color: '#FFFFFF', stroke: '#5178C6' },
            { id: 'infra', name: '基础设施', role: '8 人', color: '#FFFFFF', stroke: '#5178C6' },
          ]},
        { id: 'data-vp', name: '数据 VP', role: '陈某', color: '#F0F4FC', stroke: '#5178C6' },
      ]},
    { id: 'cpo', name: 'CPO 王五', role: '产品负责人', color: '#DFF5E5', stroke: '#509863',
      children: [
        { id: 'design', name: '设计团队', role: '6 人', color: '#FFFFFF', stroke: '#509863' },
        { id: 'research', name: '用户研究', role: '3 人', color: '#FFFFFF', stroke: '#509863' },
      ]},
    { id: 'cfo', name: 'CFO 赵六', role: '财务负责人', color: '#FEE3E2', stroke: '#D25D5A',
      children: [
        { id: 'fin-vp', name: '财务 VP', role: '5 人', color: '#FFFFFF', stroke: '#D25D5A' },
      ]},
  ],
};

const nodeW = 200, nodeH = 70, vGap = 100, hGap = 40;

// 第一遍：计算每个节点的 subtreeWidth（叶子=nodeW，非叶=children 之和+gap）
function measure(n) {
  if (!n.children || n.children.length === 0) {
    n.subtreeW = nodeW;
    return nodeW;
  }
  let w = 0;
  n.children.forEach((c, i) => {
    w += measure(c);
    if (i < n.children.length - 1) w += hGap;
  });
  n.subtreeW = Math.max(nodeW, w);
  return n.subtreeW;
}

// 第二遍：给每个节点分配 x/y
function place(n, x, y) {
  n.x = x + (n.subtreeW - nodeW) / 2;
  n.y = y;
  if (!n.children || n.children.length === 0) return;
  let cx = x;
  for (const c of n.children) {
    place(c, cx, y + nodeH + vGap);
    cx += c.subtreeW + hGap;
  }
}

measure(tree);
const totalW = tree.subtreeW + 160;
place(tree, 80, 140);
const totalH = (function depth(n) {
  if (!n.children) return 1;
  return 1 + Math.max(...n.children.map(depth));
})(tree) * (nodeH + vGap) + 80;

const nodes = [];
nodes.push({ type: "rect", x: 0, y: 0, width: totalW, height: totalH, fillColor: "#FFFFFF", borderWidth: 0 });
nodes.push({ type: "text", x: 80, y: 60, width: totalW - 160, height: 36,
  text: [{ content: titleText, bold: true, fontSize: 22 }], textAlign: "left" });

function emit(n, parentId) {
  nodes.push({
    type: "rect", id: n.id, x: n.x, y: n.y, width: nodeW, height: nodeH,
    fillColor: n.color, strokeColor: n.stroke || n.color, borderWidth: 2, borderRadius: 8,
  });
  nodes.push({
    type: "text", x: n.x + 12, y: n.y + 12, width: nodeW - 24, height: 22,
    text: [{ content: n.name, bold: true, fontSize: 15, color: n.textColor || "#1F2329" }],
    textAlign: "left",
  });
  nodes.push({
    type: "text", x: n.x + 12, y: n.y + 38, width: nodeW - 24, height: 18,
    text: [{ content: n.role, fontSize: 12, color: n.textColor === "#FFFFFF" ? "#94A3B8" : "#64748B" }],
    textAlign: "left",
  });
  if (parentId) {
    nodes.push({
      type: "connector",
      connector: { from: parentId, to: n.id, fromAnchor: "bottom", toAnchor: "top",
                   lineShape: "orthogonal", endArrow: "none", lineColor: "#94A3B8", strokeWidth: 1.5 },
    });
  }
  if (n.children) n.children.forEach((c) => emit(c, n.id));
}
emit(tree, null);

fs.writeFileSync('/tmp/wb-demo/org.json', JSON.stringify({ version: 2, nodes }, null, 2));
console.log(`org.json — ${nodes.length} nodes, canvas ${totalW}x${totalH}`);
```

## 跑通

```bash
node /tmp/wb-demo/org.cjs
feishu-lark call feishu_whiteboard '{"action":"draw","doc_id":"<doc_url>","input_path":"/tmp/wb-demo/org.json","from":"dsl"}'
```

## 陷阱

1. **同级节点过多**：> 8 个挤死。改为按部门分组 + 折叠
2. **层级过深**：> 5 层可读性差，分子图（每个 VP 单独画）
3. **连线交叉**：上面脚本里的 measure-then-place 自动处理；手写无法保证不交叉
4. **没有视觉层级**：CEO 黑色 + 部门头浅色 + 员工白色，层级一目了然
5. **CEO 等高管要醒目**：用深色填充 + 白色文字打头阵
