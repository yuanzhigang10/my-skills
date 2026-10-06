# 场景：分层泳道执行链路 / Layered Swimlane Flow

> 一种工程领域**最高频**的复杂可视化：把系统按层切分（如 API/服务/数据/存储；或 Skill/Engine/Data/Output），每层内部画流程步骤，跨层用箭头表达调用 / 数据流。

## 何时用

- 描述**多层系统**的端到端处理流程（系统架构 + 时序混合）
- 步骤多（≥ 6 个）、跨多个抽象层、需要展示**子流程**
- 适合：Skill 执行链路、微服务调用链、数据 pipeline、CI/CD 流水线

## Content 约束

- **泳道 3-6 层**（少于 3 层用简单流程图；多于 6 层视觉拥挤、拆图）
- **每层步骤 1-5 个**（步骤多时用嵌套子流程区表示）
- **全图编号步骤 ≤ 15 个**（超出认知极限）
- **配套一个嵌套子流程区**（在最复杂的那层展开内部步骤）— 这是这种图的精髓

## Layout 思路

1. **每泳道是一个水平 band**（背景渐变 + 左侧标签区固定宽度 180px）
2. **泳道高度按步骤数自适应**：基础层 140px；含嵌套子流程的层 400-500px
3. **步骤卡片在泳道内水平等距分布**
4. **每个步骤左上角带编号徽章**（深色背景、白色数字、4px 圆角）
5. **跨层箭头用 polyline**（垂直 → 水平 → 垂直 三段折线）
6. **主流程实线 + 反馈/配置依赖虚线**

## 泳道配色（沿用经典色板）

| 层 | 色相 | 浅底 | 标签底 | 边框 / 文字 |
|---|---|---|---|---|
| 接入 / 用户 | 紫 | `#F4EEFF` | `#EAE2FE` | `#8569CB` |
| API / 接口 | 蓝 | `#E8EFFF` | `#E1EAFF` | `#5178C6` |
| 数据 / 配置 | 绿 | `#E6F6E9` | `#DFF5E5` | `#509863` |
| 计算 / 引擎 | 黄 | `#FFF7E0` | `#FEF1CE` | `#D4B45B` |
| 输出 / 落地 | 薄荷绿 | `#E5F8EE` | `#DFF5E5` | `#3C8B6B` |

## SVG 骨架（写法范式）

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1800 1300">
  <defs>
    <!-- 每层一对渐变 -->
    <linearGradient id="laneA" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#F4EEFF"/>
      <stop offset="1" stop-color="#FFFFFF"/>
    </linearGradient>
    <!-- 每色一个 arrow marker -->
    <marker id="arrA" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#8569CB"/>
    </marker>
  </defs>

  <!-- 1. 标题 -->
  <text x="900" y="60" font-size="32" text-anchor="middle" font-weight="800" fill="#1F2329">{{标题}}</text>
  <text x="900" y="92" font-size="14" text-anchor="middle" fill="#646A73">{{副标题}}</text>

  <!-- 2. 整体外框 -->
  <rect x="40" y="130" width="1720" height="1130" rx="16" fill="#FFFFFF" stroke="#E5E6EB" stroke-width="1.5"/>

  <!-- 3. 单泳道结构 -->
  <rect x="40" y="130" width="1720" height="160" rx="16" fill="url(#laneA)"/>
  <rect x="40" y="130" width="180" height="160" rx="16" fill="#EAE2FE"/>
  <!-- 标签图标 (SVG 自由发挥) -->
  <circle cx="130" cy="195" r="22" fill="#FFFFFF" stroke="#8569CB" stroke-width="2"/>
  <!-- 标签文字 -->
  <text x="130" y="252" font-size="16" font-weight="700" text-anchor="middle" fill="#8569CB">Skill 层</text>

  <!-- 4. 步骤卡片（含编号徽章）-->
  <rect x="260" y="170" width="220" height="80" rx="10" fill="#FFFFFF" stroke="#8569CB" stroke-width="2"/>
  <rect x="276" y="180" width="28" height="20" rx="4" fill="#8569CB"/>
  <text x="290" y="195" font-size="12" text-anchor="middle" fill="#FFFFFF" font-weight="700">01</text>
  <text x="320" y="198" font-size="17" font-weight="700" fill="#1F2329">用户问题</text>
  <text x="276" y="225" font-size="12" fill="#646A73">用户提出归因问题</text>

  <!-- 5. 同层箭头 -->
  <line x1="480" y1="210" x2="540" y2="210" stroke="#8569CB" stroke-width="2" marker-end="url(#arrA)"/>

  <!-- 6. 跨层箭头（polyline 三段折线）-->
  <polyline points="660,270 660,300 380,300 380,340" stroke="#5178C6" stroke-width="2" fill="none" marker-end="url(#arrB)"/>

  <!-- 7. 嵌套子流程区（在最复杂的那层）-->
  <rect x="260" y="660" width="1480" height="390" rx="14" fill="#FFFFFF" stroke="#D4B45B" stroke-width="2"/>
  <rect x="278" y="675" width="34" height="20" rx="4" fill="#D4B45B"/>
  <text x="295" y="690" font-size="12" text-anchor="middle" fill="#FFFFFF" font-weight="700">10</text>
  <text x="325" y="693" font-size="17" font-weight="700" fill="#1F2329">归因计算引擎内部流程</text>
  <!-- 子区内放：标准输入区(绿) + 4 阶段卡片 + 标准输出区(紫) -->

  <!-- 8. 反馈/依赖虚线 -->
  <polyline points="1100,1175 1740,1175 1740,210 1720,210" stroke="#8569CB" stroke-width="2" stroke-dasharray="6 4" fill="none" marker-end="url(#arrA)"/>
</svg>
```

## 编号徽章惯例

```xml
<!-- 徽章：深色底 + 白色数字 + 圆角 -->
<rect x="..." y="..." width="28" height="20" rx="4" fill="{layerColor}"/>
<text x="..." y="..." font-size="12" text-anchor="middle" fill="#FFFFFF" font-weight="700">01</text>
```

宽度建议 28-34px（容纳 2 位数字），高度 18-22px。位置在步骤卡左上角内缩 16px。

## 步骤卡片惯例

每个步骤卡固定结构：
- **顶行**：编号徽章 + 标题（17-18px bold）
- **下方**：1-3 行说明（12-13px 灰色 `#646A73`）
- 整卡 `borderRadius: 10`、`borderWidth: 2`、白底 + 该层色边框
- 宽度根据内容 200-260px，高度 80-100px

## 跨层箭头模式

| 用途 | 走线 | 样式 |
|---|---|---|
| 主流程下钻（A → B → C）| 出发点 →下 → 水平 → 入终点 | 实线 + 终点色 |
| 配置依赖（虚） | 同上 | 虚线 `stroke-dasharray="6 4"` |
| 反馈环（输出 → 入口）| 沿外框右侧绕回顶部 | 虚线 + 起点色 |

## 嵌套子流程区

最复杂的那层（通常是"计算"或"处理"层）展开内部步骤：
- 子区是该层泳道内的一个大白色 rect（`borderColor: {layerColor}`、`borderWidth: 2`）
- 子区左上角放一个总编号徽章（如 `10`） + 总标题
- 子区**内部用同样的"步骤卡 + 子箭头"模式**，子编号 01-04
- 子区两端可放：**左侧"标准输入"小区**（含 1-3 个输入卡）、**右侧"标准输出"小区**（含 1-4 个输出卡）

## 跑通 + 入文档

```bash
mkdir -p /tmp/wb-demo

# 直接写 SVG 到 /tmp/wb-demo/<name>.svg
# 渲染预览
feishu-lark call feishu_whiteboard '{"action":"render","input_path":"/tmp/wb-demo/layered-flow.svg"}'

# 入文档（width × height 必须等于 SVG viewBox）
feishu-lark call feishu_whiteboard '{
  "action": "draw",
  "doc_id": "<doc_url>",
  "input_path": "/tmp/wb-demo/layered-flow.svg",
  "width": 1800,
  "height": 1300
}'
```

## 设计要点

1. **泳道带左侧 180px 固定标签区**：图标 + 中文标签竖排，统一对齐
2. **泳道背景用横向渐变**（左浓右淡）：左侧标签区色块明显，右侧步骤区柔和过渡到白色
3. **同层不同步骤同色但徽章变化**：编号徽章统一该层主色，区分步骤靠标题文字
4. **同层箭头水平短直线 + 同色 marker**：实线表示串行依赖
5. **跨层箭头用 polyline 三段折线**：避免穿越其他步骤卡，建议沿泳道边缘走
6. **虚线代表"非主流程"**：配置加载、就绪检查、反馈环都用虚线
7. **嵌套子流程区只在 1 层出现**：避免视觉碎片化
8. **子区两端可挂"输入/输出"小区**：用不同色（如绿色输入、紫色输出）跟主子流程区分

## 陷阱

1. **泳道高度算不对**：嵌套子流程层 ≥ 400px，其他层 140-160px。算总 height 时务必加起来。
2. **左侧标签区与渐变冲突**：标签区是**固定色块**（饱和度更高），渐变只在右侧步骤区。两者用相邻的两个 rect。
3. **跨层箭头穿越卡片**：polyline 中间路径要走"夹缝"——查所有卡片的 x 范围，绕开。
4. **编号顺序混乱**：全图编号 01-12 是一条线（用户问题 → 渲染），子区内编号 01-04 是另一条线。**不要全图统一编号**。
5. **箭头 marker 不显示**：每个颜色一个 `<marker>` 定义。`refX="9"` 保证箭头不被覆盖。`orient="auto-start-reverse"` 让反向箭头也能用。
6. **跨层箭头与跨层文字标签冲突**：箭头路径不要叠到泳道标签区。
7. **图过宽 > 2000**：飞书 docx 渲染较慢，建议拆成两张连续画板。
