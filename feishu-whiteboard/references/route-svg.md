# Route: SVG ⭐ 推荐主路径

SVG 是飞书画板**最强大、最灵活**的输入方式。本工具实测：**渐变、径向光晕、弧光、玻璃质感卡片**——这些视觉效果**全部能稳定渲染**，多数还能保留为可编辑节点。

> 在 demo 文档 §4（[doc URL](https://www.feishu.cn/docx/UHzVdf0vAogLgex3wL8lEA7Agjh)）有完整范例：暗夜主题 + 双色光晕 + 弧光线条 + 玻璃卡片，19 个 text + 13 个形状 + 3 个 connector + 2 个 svg 容器全部上传成功。

## 核心心智

> **大多数 AI 默认输出"白底网格 + 一堆 rect"，这是不及格的。**
>
> SVG 给你**真正的设计自由**——自定义图标路径、流畅曲线、装饰物、光影氛围。**充分信任你的艺术直觉**，不要怯于使用渐变和复杂图形。

正在设计的是**信息图**，不是网页线框稿：
- **核心信息**：一图胜千言。先想要传达的洞察，再选视觉语言
- **内容充实度**：用户描述稀疏时，用领域知识扩展信息维度（但不堆砌）
- **视觉隐喻**：金字塔=层级 / 飞轮=循环 / 桑基=分流 / 雷达=多维 / 光晕=焦点
- **大胆用色**：从 [`style.md`](style.md) 挑色板；深色主题也欢迎

## 飞书画板支持的 SVG 元素

### ✅ 完全支持（解析为可编辑节点）

| 元素 | 飞书节点 type | 备注 |
|---|---|---|
| `<rect>` | composite_shape rect/round_rect | `rx` > 0 → round_rect |
| `<circle>` / `<ellipse>` | composite_shape ellipse | — |
| `<polygon>` | composite_shape | 多边形 |
| `<path>` | connector / svg | 直线 / 折线 / 曲线自动识别 |
| `<line>` / `<polyline>` | connector | — |
| `<text>` / `<tspan>` | text_shape | 中文 hardcoded Noto Sans SC |
| `<g>` / `<use>` / `<a>` | group | 分组 |
| `transform: translate/rotate/scale` | 应用到节点 | 正常 |

### ✅ 支持但作为内嵌图片渲染（不可二次编辑，但视觉保留）

| 元素 | 渲染效果 | 推荐使用 |
|---|---|---|
| `<linearGradient>` | ✅ 完美渲染 | 渐变背景、按钮、阴影区域 |
| `<radialGradient>` | ✅ **完美渲染**（实测光晕效果惊艳）| 焦点光晕、聚光、能量发散 |
| `<filter>` 简单滤镜 | ⚠️ 部分支持 | 不可靠，建议避开 |
| `<defs>` + `<stop>` 多色渐变 | ✅ | 复杂渐变 |
| `stroke="url(#grad)"` 渐变描边 | ✅ | 弧光、流光线条 |
| `transform: matrix/skew` | 降级为图片 | 慎用 |

### ❌ 不支持（用了会渲染失败）

| 元素 | 影响 |
|---|---|
| `<clipPath>` | 整张图渲染失败 |
| `<mask>` | 整张图渲染失败 |
| `<pattern>` | 渲染异常 |
| `<filter id="blur">` 高斯模糊 | 飞书侧可能丢失模糊效果 |

## Workflow

```bash
# 1. 创目录
mkdir -p /tmp/wb-demo

# 2. 写 SVG
cat > /tmp/wb-demo/diagram.svg <<'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900">
  ...
</svg>
EOF

# 3. 本地渲染 + 检查
feishu-lark call feishu_whiteboard '{"action":"render","input_path":"/tmp/wb-demo/diagram.svg"}'
# Read 返回的 output_path 看 PNG 自检

# 4. 入文档（width/height 必须等于 SVG 的 viewBox）
feishu-lark call feishu_whiteboard '{
  "action": "draw",
  "doc_id": "<doc_url>",
  "input_path": "/tmp/wb-demo/diagram.svg",
  "width": 1600,
  "height": 900
}'
```

## 高级范式（可复用）

### 1. 渐变背景（瞬间提升质感）

```xml
<defs>
  <linearGradient id="bgGrad" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#0F172A"/>
    <stop offset="1" stop-color="#1E293B"/>
  </linearGradient>
</defs>
<rect x="0" y="0" width="1600" height="900" fill="url(#bgGrad)"/>
```

科技风暗色基底。同色系：商务蓝紫、能量橙红、自然绿青。

### 2. 径向光晕（焦点、能量、热点）

```xml
<defs>
  <radialGradient id="glow" cx="50%" cy="50%" r="50%">
    <stop offset="0" stop-color="#38BDF8" stop-opacity="0.95"/>
    <stop offset="0.6" stop-color="#38BDF8" stop-opacity="0.3"/>
    <stop offset="1" stop-color="#38BDF8" stop-opacity="0"/>
  </radialGradient>
</defs>
<circle cx="380" cy="280" r="320" fill="url(#glow)"/>
```

把光晕放在 **暗色背景** + **半透明叠加** + **大半径**，瞬间获得"赛博朋克"质感。

### 3. 弧光线条（渐变描边）

```xml
<defs>
  <linearGradient id="arcLight" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#38BDF8" stop-opacity="0"/>
    <stop offset="0.5" stop-color="#38BDF8" stop-opacity="1"/>
    <stop offset="1" stop-color="#A78BFA" stop-opacity="0"/>
  </linearGradient>
</defs>
<path d="M 0 200 Q 800 100 1600 250"
      stroke="url(#arcLight)" stroke-width="3" fill="none"/>
```

两端透明 + 中间不透明 = 光带从无到有再消失。配合 cubic-bezier 弯曲 = 流光弧线。

### 4. 玻璃质感卡片

```xml
<defs>
  <linearGradient id="card" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#1E293B" stop-opacity="0.95"/>
    <stop offset="1" stop-color="#0F172A" stop-opacity="0.85"/>
  </linearGradient>
</defs>
<rect x="200" y="380" width="340" height="220" rx="20"
      fill="url(#card)" stroke="#38BDF8" stroke-width="1.5"
      opacity="0.92"/>
```

半透明渐变 + 细描边 + 大圆角 = "毛玻璃"质感。配合暗色背景 + 光晕，整体仪表盘风格。

### 5. 阴影模拟（绕过 `<filter>` 不支持）

```xml
<rect x="102" y="102" width="200" height="100" rx="8" fill="#1F2329" opacity="0.1"/>
<rect x="100" y="100" width="200" height="100" rx="8" fill="#FFFFFF" stroke="#5178C6"/>
```

错位绘制 + 半透明深色 = 卡片浮起感，比 `<filter>` 更稳。

## 跨场景灵感

不要只画卡片！下列视觉语言**都能用纯 SVG 实现**：

| 场景 | 关键元素 |
|---|---|
| 暗夜主题 dashboard | 渐变背景 + 双色光晕 + 玻璃卡片 + 弧光线条 |
| 海报 / 活动宣传 | 斜切几何色块 + 大字标题 + 渐变线条堆叠 + QR 占位 |
| 平面图 / 建筑制图 | 嵌套 `<rect>` 表墙体厚度 + `<path>` 弧线表门开启 + 功能区色块 |
| 地铁线路图 | 多色 `<polyline>`（仅水平 / 垂直 / 45° 折角）+ `<circle>` 站点 + 换乘双圈 |
| 仪表盘 mockup | 圆角 `<rect>` 卡片 + `<path>` 平滑数据曲线 + 环形图弧段 + 深色侧边栏 |
| 雷达图 | 多边形栅格 + 中心点辐射 + 数据多边形覆盖 |
| 桑基图 | 三列节点矩形 + cubic-bezier 流条 + 流条宽度精确等于流量值 |
| 价值金字塔 | 多层梯形宽度按斜率系数递减 + 冷暖色渐变 + 右侧描述外置 |
| 鱼骨图 | 主骨水平 + 斜分支 + 三角函数等距挂载 + 同色系分组 |
| 流量飞轮 | 大圆切割 + 极坐标外围卡片 + 中心标题 |
| 思维导图（自由）| 中心圆 + 辐射枝干 + 末端文字标签 + 不同枝干不同色 |
| 信息图 | 大数字 + 短结论 + 装饰图标 + 配色板 |
| 时序图（自由）| 上下泳道 + 水平时间线 + 实虚线区分同步/异步 |

## 实战要点

### 极坐标布局

```js
const cx = 600, cy = 400, r = 280;
for (let i = 0; i < N; i++) {
  const θ = (i / N) * 2 * Math.PI - Math.PI / 2;
  const x = cx + r * Math.cos(θ);
  const y = cy + r * Math.sin(θ);
}
```

### cubic bezier 平滑曲线

```xml
<path d="M 300 100 C 500 100, 500 250, 700 250" ... />
```

`C` 的 4 个参数：控制点 1、控制点 2、终点。控制点距离决定曲率。

### 中文字体

飞书画板硬编码 Noto Sans SC。SVG 写 `font-family="..."` 实际会被忽略，所以**不必专门指定**。但 `font-weight="700"` / `font-style="italic"` 都正常生效。

## 检查清单（交付前）

- [ ] viewBox 与 draw 时传的 width×height 完全一致
- [ ] 所有文字用 `<text>`，没有用 `<path>` 写汉字
- [ ] 未使用 `<clipPath>` `<mask>` `<pattern>`
- [ ] 至少包含一种视觉隐喻（不是纯 grid 网格卡片）
- [ ] 同分组用同色系，色相差异显著
- [ ] 关键信息有视觉锚点（黑色块 / 强调色 / 形状变化）
- [ ] 暗色主题：使用渐变背景而非纯黑，避免单调
- [ ] 渐变 / 光晕 / 弧光至少用了一种（信息图都该有装饰元素）

## 双轨：失败时切 DSL

SVG 路径**两次自查后仍然丑或不渲染**，**丢弃 SVG，改走 [`route-dsl.md`](route-dsl.md)** 从零重画。SVG 源码修补常引入新 bug，换 DSL 用 .cjs 脚本算坐标往往更稳。
