# 工程蓝图风格（Blueprint）

当用户提到"blueprint 风格"、"工程蓝图"、"分层架构封层图"、"覆盖热力图"、"治理路线图"、"旅程泳道"、"保持那种画板风格一致"时，优先走本参考。它不是独立工具，而是 `feishu_whiteboard` 的一套固定视觉系统和 SVG 模板。

## 适用场景

| 用户意图 | 推荐模板 |
|---|---|
| 分层架构 / 封层图 | `templates/blueprint/layered-bands.svg` |
| PRD → Code → QA 主轴 / 横向阶段 + 知识总线 | `templates/blueprint/phased-pipeline.svg` |
| 域 × 动作覆盖度矩阵 / 空白扫描 | `templates/blueprint/coverage-heatmap.svg` |
| 治理路线图 / 里程碑 / Gantt-lite | `templates/blueprint/milestone-timeline.svg` |
| 指标体系 / 三层金字塔 | `templates/blueprint/tier-pyramid.svg` |
| 单条 PRD/任务旅程 / 泳道 | `templates/blueprint/journey-swimlane.svg` |

不适合：营销海报、轻量草图、普通 Mermaid 关系图、需要彩色插画感的内容。那些继续走通用 whiteboard / SVG / Mermaid 路径。

## 工作流

1. 选模板并复制到 `/tmp/wb-demo/<name>.svg`。
2. 替换标题、副标题、主体文本、指标和 footer insights。保留模板的 viewBox、标题区、图例区、footer 区。
3. 本地检查：

```bash
feishu-lark call feishu_whiteboard '{"action":"check","input_path":"/tmp/wb-demo/blueprint.svg","from":"svg"}'
feishu-lark call feishu_whiteboard '{"action":"render","input_path":"/tmp/wb-demo/blueprint.svg","from":"svg"}'
```

4. 读 `render` 返回的 PNG 自检视觉效果。`text-overflow` 对分层/嵌套 rect 有时是误报，先看图。
5. 写入文档：

```bash
feishu-lark call feishu_whiteboard '{
  "action": "draw",
  "doc_id": "<doc_url 或 doc_id>",
  "input_path": "/tmp/wb-demo/blueprint.svg",
  "from": "svg",
  "width": 1400,
  "height": 720
}'
```

6. 上传后如用户反馈缺内容，先用 `list_nodes` 或服务端截图路径核验，再判断是数据缺失还是飞书客户端渲染/viewport 问题。

## 视觉法则

### 四层语义色

| 层 | 用途 | 填充 | 描边 | 编号底色 | 文字 |
|---|---|---|---|---|---|
| ① Top / 编排 / Triage | 入口路由、分诊、何时调用什么 | `#dcf2dc` | `#84c184` | `#3a8a3a` | `#1f2937` |
| ② Upper-mid / 上下文 / Inputs | 上下文加载、知识获取、输入治理 | `#fde6dc` | `#e89890` | `#c75050` | `#1f2937` |
| ③ Main axis / 流程主轴 / Pipeline | PRD→Code→QA 主链路、阶段推进 | `#fdf3cb` | `#d4b850` | `#a07c20` | `#1f2937` |
| ④ Bottom / 横切 / Cross-cut | 贯穿式工具、监控、审计、发布 | `#e0e8f7` | `#7e96d4` | `#4862a8` | `#1f2937` |

数据状态：

- 空白 / gap：`fill="#fff5f5" stroke="#dc2626" stroke-width="1.5" stroke-dasharray="3,2"`，文字 `#dc2626`
- 热力图 5 桶：`#eef2f6` → `#c6dcef` → `#6b9bcf` → `#2e5e9a` → `#1a3a6b`
- 深色热力单元文字用 `#fff`，浅色单元文字用 `#1f2937`

### 字体

只用两类字体：

```text
Noto Sans SC, -apple-system, sans-serif
JetBrains Mono, monospace
```

- 标题：22-24px, 700, `#1f2937`
- 副标题：12-13px, `#6b7280`
- 层标题：15px, 700
- 层副标题 / 编号 / 技术标签：JetBrains Mono，10-11px
- Caption / footer：9.5px，`#6b7280`，可 italic

技术标识、skill 名、事件名、里程碑 ID、数据值必须用 JetBrains Mono。

## 布局约定

- 顶部必须有 title + subtitle，留足 80px 以上安全边距。
- y=84-120 区域放 legend 或 reading-order strip。
- 分层图使用编号圆点 `①②③④`，圆点填充用对应层的编号底色。
- 连接线优先正交：水平、垂直、90 度折线。主流程不要为了装饰画斜线。
- consult / knowledge bus 这类弱依赖使用 dashed line：`stroke-dasharray="3,3"`。
- 大段结构标题可用 28px 深色横条，白色 mono 大写。
- 每张图底部必须有 1-3 条 footer insights，解释这张图的结论，不只画形状。

## 硬规则

- 不用阴影、渐变、玻璃拟态。Blueprint 要像工程 spec sheet，不像营销视觉。
- 不用随机彩虹色。结构色只从四层语义色里选。
- 不用 emoji 当核心视觉。
- 内容块 `rx` 不超过 8；不要做大号 pill。
- 空白、缺口、风险必须用红色虚线约定，让读者 0.5 秒看到问题。
- 一张图尽量控制在 150 节点以内；内容太多就拆多张。

## 飞书渲染防御

飞书本地 SVG 预览、服务端渲染、浏览器画板 canvas 是三条不同路径。遇到"本地图正确但文档里缺一块"时，按这个顺序判断：

| 本地 PNG | 服务端/节点数据 | 用户浏览器 | 判断 |
|---|---|---|---|
| 正确 | 正确 | 缺内容 | 客户端渲染或 viewport clipping，让用户刷新、双击全屏、等待 3-5 秒 |
| 正确 | 缺内容 | 缺内容 | SVG → OpenAPI 转换丢节点，简化 SVG 后重传 |
| 缺内容 | 缺内容 | 缺内容 | SVG 本身错误，先修 SVG |

防御性写法：

- 顶部关键内容不要放在前 60px。
- 少用 `<g>` 继承字体属性，重要文字把 `font-size` / `font-family` 写在 `<text>` 上。
- 大外层 rect 不要用饱和填充再套小 rect。超过 800×80 的层级底板优先用近白色，如 `#f6fcf6`，或 `fill="none"`。
- 深色实心块 + 白字是最容易在浏览器里出现文字消失的组合。必须用时加明确 stroke，并控制节点数量。
- band rect 先画，子 rect 和文字后画，靠 SVG painter order 保证层级。

## 模板维护

`templates/blueprint/*.svg` 是完整可渲染示例。改模板时必须先跑 `feishu_whiteboard action=check` 和 `render`，再抽样 `draw` 到测试文档确认飞书端可编辑。
