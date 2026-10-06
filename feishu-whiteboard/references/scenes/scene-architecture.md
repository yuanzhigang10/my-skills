# Scene: 系统架构图（分层 / 模块依赖）

> **混合用 SVG 或 DSL 都行**。简单架构（3-5 层、< 20 节点）首选 SVG（自由控制视觉）；复杂模块依赖（节点 > 20、关系网密）首选 DSL + dagre layout。

## 何时用

- **系统架构**：前端 → API → 服务 → 数据 的端到端架构图
- **微服务依赖**：多服务相互调用、消息队列、共享存储
- **技术栈展示**：技术选型 / 工程栈分层（容器/编排/CICD/监控）
- **避免与流程图混淆**：架构图强调"组件分层和关系"，不是时间序列

## Content 约束

- **3-6 层**（如 客户端 / API / 服务 / 缓存 / 数据库 / 第三方）
- **每层 2-6 个组件**（多于 6 拆子图或聚合）
- **每个组件**：icon + name + 1-2 行说明（技术栈 / 关键能力）
- **关系**：层间用箭头表示主流程；层内可用虚线表示横向调用

## Layout 思路（推荐 SVG）

- **横向 band 分层**：每层一个高度 ≥ 160px 的水平条，背景渐变（左浓右淡）
- **左侧标签区固定 180px**：图标 + 层名（参考 `scene-layered-flow.md`）
- **组件卡片在层内等距排列**：宽度 220-280px，高度 90-110px
- **箭头多色编码**：每层主色一种颜色 + markers
- **配色用 5 色板**（参见 [`style.md`](style.md)）：紫客户端 / 蓝 API / 绿数据 / 黄计算 / 薄荷绿输出

## SVG 骨架（缩略）

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1800 1200">
  <defs>
    <linearGradient id="laneClient" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#EAE2FE"/><stop offset="1" stop-color="#FFFFFF"/>
    </linearGradient>
    <marker id="arrPurple" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#8569CB"/>
    </marker>
    <!-- 每层一对：lane gradient + arrow marker -->
  </defs>

  <text x="900" y="50" font-size="32" text-anchor="middle" font-weight="800" fill="#1F2329">系统架构</text>

  <!-- 泳道 1：客户端 -->
  <rect x="40" y="100" width="1720" height="200" rx="16" fill="url(#laneClient)"/>
  <rect x="40" y="100" width="180" height="200" rx="16" fill="#EAE2FE"/>
  <lucide name="monitor" x="80" y="150" size="48" stroke="#8569CB"/>
  <text x="130" y="240" font-size="16" font-weight="700" text-anchor="middle" fill="#8569CB">Client</text>

  <!-- 组件卡片 × N -->
  <rect x="260" y="140" width="240" height="120" rx="10" fill="#FFFFFF" stroke="#8569CB" stroke-width="2"/>
  <lucide name="globe" x="276" y="156" size="28" stroke="#8569CB"/>
  <text x="320" y="174" font-size="16" font-weight="700" fill="#0F172A">Web Browser</text>
  <text x="276" y="206" font-size="12" fill="#64748B">React · Next.js</text>
  <text x="276" y="226" font-size="12" fill="#64748B">PWA · Service Worker</text>

  <!-- 跨层箭头 -->
  <polyline points="380,260 380,290 380,320" stroke="#8569CB" stroke-width="2" fill="none" marker-end="url(#arrPurple)"/>
</svg>
```

## 完整范例

实际范例见 demo 文档 §1 ([URL](https://www.feishu.cn/docx/ZrFZdWPEvoPhAZxtKSklLdZygqe))：「Next.js 14 全栈 React 架构」 — 5 层、25 个组件卡、4 色跨层箭头、RSC 直读 DB 虚线、revalidate 反馈环。

## Lucide 图标推荐

| 层 | 推荐图标 |
|---|---|
| 客户端 | `monitor` / `smartphone` / `globe` / `users` / `cloud` |
| API / Edge | `code` / `webhook` / `shield-check` / `git-pull-request` / `bot` |
| 状态 / 缓存 | `git-branch` / `refresh-cw` / `sparkles` / `network` / `loader` |
| 计算 / 服务 | `cpu` / `brain-circuit` / `server` / `zap` / `bot` |
| 数据 / 持久化 | `database` / `hard-drive` / `image` / `search` / `external-link` |

## 跨层箭头模式

| 用途 | 走线 | 样式 |
|---|---|---|
| 主请求（A → B → C）| 出发点 → 下 → 水平 → 入终点 | 实线 + 终点色 |
| 配置 / 依赖（虚）| 同上 | 虚线 `stroke-dasharray="6 4"` |
| 反馈环 / 回写 | 沿外框右侧绕回顶部 | 虚线 + 弱色 |
| 跨层直通（如 RSC 直读 DB）| 曲线绕开中间层 | 虚线 + 斜体注释 |

## 陷阱

1. **箭头穿卡片**：polyline 走"夹缝"——查所有卡片 x 范围，绕开
2. **箭头与文字标签冲突**：箭头路径不要叠到标签区
3. **图过宽 > 2000**：飞书 docx 渲染慢，建议拆成两张
4. **箭头颜色无规律**：每"种"数据流一种颜色 + 一种 marker，图例底部标明
5. **节点描述太长**：单卡 ≤ 2 行 desc，超出需精简
