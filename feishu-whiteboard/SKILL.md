---
name: feishu-whiteboard
description: |
  飞书画板（Whiteboard）操作 — 在飞书云文档内创建可编辑的画板节点。覆盖根因分析（鱼骨）、增长飞轮、产品路线图、工程蓝图/Blueprint、价值金字塔、桑基流、组织架构、UI mockup、海报等专业可视化作品。
  通过 feishu-lark CLI 调用。

  当以下情况时使用：
  (1) 用户要把图表/信息图/流程图嵌入飞书云文档
  (2) 用户提到"画板"、"whiteboard"、"画图"、"鱼骨"、"飞轮"、"路线图"、"blueprint"、"工程蓝图"、"覆盖热力图"、"flowchart"、"信息图"、"可视化"
  (3) 需要将 SVG / Mermaid / DSL JSON / PlantUML 转成可编辑的飞书画板节点
  (4) 操作已有画板：补节点、读节点、改主题
---

# 飞书画板 (Whiteboard)

## 核心心智（必读，决定输出质量）

**不要做出"白底网格 + 一堆 rect" 的图**。

很多 AI 在生成画板时为了"完全不出错"，最终交付的全是清一色白底矩形网格，毫无信息层级和视觉张力 —— **这种输出视为不及格**。

正确姿态：
- **先想画什么**：核心信息是什么？能不能一图胜千言？信息维度够不够？有没有视觉隐喻（金字塔=层级、飞轮=循环、桑基=分流）？
- **充分使用色彩与几何**：从经典色板里挑 3-5 套同色系（[`references/style.md`](references/style.md)），不同分组用不同色系。
- **几何复杂的场景必须脚本生成**：鱼骨/飞轮/桑基/路线图/金字塔的坐标都要算，**手写 JSON 必定重叠**。用 [`references/scene-*.md`](references/) 里的脚本模板。
- **不要塞太多东西到一张图**：一图一主题，画不下就拆多张。

---

## 决策树

```
用户要什么？
│
├─ 想在飞书文档里画一张图
│   ├─ 是哪种图？
│   │   ├─ 工程蓝图/分层架构/覆盖热力图/泳道 → blueprint-style.md（SVG 模板）
│   │   ├─ 流程图/时序图/类图/状态图/ER  → routes/mermaid.md（直接喂 mermaid）
│   │   ├─ 鱼骨图                       → scene-fishbone.md（脚本生成 DSL）
│   │   ├─ 飞轮 / 闭环                  → scene-flywheel.md（脚本生成 DSL）
│   │   ├─ 路线图 / 时间轴 / 里程碑     → scene-roadmap.md（脚本生成 DSL）
│   │   ├─ 海报 / 插画 / UI mockup      → routes/svg.md（自由 SVG）
│   │   └─ PlantUML 时序/类图           → action: create_plantuml（飞书原生）
│   └─ 渲染 → draw 进文档
│
├─ 已经有画板，要 ...
│   ├─ 加新内容              → action: add_nodes（务必开 auto_below）
│   ├─ 列出已有节点          → action: list_nodes
│   ├─ 改主题                → action: update_theme
│   └─ 不想动 ID，先本地预览 → action: render
│
└─ 一篇文档多张图 → 多次 draw（每张独立画板，不会互相重叠）
```

> **⚠️ 一图一画板**：不要把多张无关的图塞到同一画板里——新节点会与现有内容堆叠在原点。多张图用多次 `draw`，每张图独立画板。

---

## Workflow：从需求到画板

### Step 1 · 选择画法

按图表类型选路径（前置阅读对应文件）：

| 图表类型 | 路径 | 写法 |
|---|---|---|
| 工程蓝图 / blueprint / 分层架构 / 覆盖热力图 / 泳道 | [`references/blueprint-style.md`](references/blueprint-style.md) | 复制 `templates/blueprint/*.svg` 后改内容 |
| flowchart / sequence / class / state / ER / pie / mindmap | [`references/route-mermaid.md`](references/route-mermaid.md) | 直接 mermaid 字符串 |
| 鱼骨 / 飞轮 / 路线图 / 金字塔 / 桑基 | [`references/scene-*.md`](references/) | 脚本生成 DSL JSON |
| 海报 / 插画 / UI mockup / 平面图 / 自定义图表 | [`references/route-svg.md`](references/route-svg.md) | 手写 SVG |
| PlantUML 时序/类/活动图 | 直接 `create_plantuml` action | PlantUML 代码 |

### Step 2 · 生成原料

| 路径 | 操作 |
|---|---|
| Mermaid | 直接写字符串 → `content` 或 `input_path` |
| DSL JSON | `node /tmp/wb-demo/scene.cjs` → 输出 `/tmp/wb-demo/scene.json` |
| SVG | `cat > /tmp/wb-demo/diagram.svg <<EOF ... EOF` |

> 所有本地路径**必须在 os.tmpdir() 或 /tmp 下**——其他路径被白名单拒绝。

### Step 3 · 本地预览（强烈推荐）

```bash
feishu-lark call feishu_whiteboard '{"action":"render","input_path":"/tmp/wb-demo/scene.json","from":"dsl"}'
```

工具返回 `output_path: /tmp/feishu-lark-wb/<uuid>.png`，Read 这个 PNG 路径自检视觉效果。差就回到 Step 2 调整脚本/SVG，不要直接 draw 到飞书然后再改。

### Step 4 · 写入飞书文档

```bash
feishu-lark call feishu_whiteboard '{
  "action": "draw",
  "doc_id": "<doc_url 或 doc_id>",
  "input_path": "/tmp/wb-demo/scene.json",
  "from": "dsl",
  "width": 1516,
  "height": 736
}'
```

返回 `{whiteboard_id, block_id, node_count, ids}`，画板已在文档末尾，节点可编辑。

### Step 5 · 多张图（推荐工作流）

按章节配套 markdown 段落 + 画板：

```bash
# 1) 先创建文档（含所有章节标题与说明）
feishu-lark call feishu_create_doc '{"title":"...","markdown":"# 标题\n\n## §1 ...\n\n## §2 ..."}'

# 2) 逐个 draw 到文档末尾（自动 append）
feishu-lark call feishu_whiteboard '{"action":"draw","doc_id":"...","input_path":"/tmp/.../1.json","from":"dsl"}'
feishu-lark call feishu_whiteboard '{"action":"draw","doc_id":"...","input_path":"/tmp/.../2.json","from":"dsl"}'

# 3) 也可在 draw 之间 update_doc append 一段说明
feishu-lark call feishu_update_doc '{"doc_id":"...","mode":"append","markdown":"## §3 ..."}'
```

---

## 关键参数（feishu_whiteboard action 速查）

| action | 必填 | 关键可选 |
|---|---|---|
| `render` | `input_path` 或 `content` | `to`(image/openapi), `output_path`, `scale`, `from` |
| `draw` ⭐ | `doc_id`, 原料 | `width`, `height`, `align`, `after_block_id`, `from` |
| `create_in_doc` | `doc_id` | `width`, `height`, `align`, `after_block_id` |
| `add_nodes` | `whiteboard`, 原料 | **`auto_below: true`**, `offset_x/y`, `from`, `batch_size` |
| `list_nodes` | `whiteboard` | - |
| `create_plantuml` | `whiteboard`, `plant_uml_code` | `syntax_type`/`diagram_type`/`style_type`（缺省全 1） |
| `get_theme` / `update_theme` | `whiteboard` (+ `theme`) | - |
| `lucide` | `icon_names: []` | 取 Lucide 图标 SVG（无依赖、无 auth） |
| `check` | `input_path` 或 `content` | 跑 whiteboard-cli `--check`：抓 text-overflow / node-overlap。强烈建议 draw 前先 check |
| `diagnose` | — | 自检：whiteboard-cli 安装、unpkg 可达、缓存目录可写、已缓存图标数 |

> SVG 输入支持 **`<lucide name="user" x="100" y="100" size="32" stroke="#5178C6"/>` 占位符**——render/draw/add_nodes 自动展开为真实 Lucide 图标。详见 [`icons-lucide.md`](references/icons-lucide.md)。

> 第一次使用前建议跑 `feishu_whiteboard {action:"diagnose"}` 一次。返回 `overall: "fail"` 时按提示修。

---

## 高频坑

1. **节点会堆叠**：`add_nodes` 默认新节点放在原点附近，与已有节点重叠。多张不同图用多次 `draw`；必须追加时开 `auto_below: true`。飞书 SDK **无删除节点 API**，做不了"清空重画"。
2. **`block_id` ≠ `whiteboard_id`**：docx 块 id 与 board.token 不同。本工具传 `docx?block=` URL 时会自动调 `documentBlock.get` 解析。直接传 token 最稳。
3. **PlantUML 三个 type 必传**：`syntax_type`/`diagram_type`/`style_type` API 实际必填（SDK 类型签名却是可选）。本工具默认全填 1，特殊风格再覆盖。
4. **节点 batch**：单次写入上限飞书侧未公开。默认 1000/批，失败自动回退到 500/250/100/50。
5. **画板 viewport**：飞书 docx 里画板块按指定 width/height 显示，超出内容需用户在画板内滚动/缩放。SVG viewBox **必须**匹配 width×height。
6. **白底矩形不及格**：用 [`references/style.md`](references/style.md) 的配色 + 几何隐喻 + 字号层级，不要堆 `<rect>`。
7. **依赖按需**：render/add_nodes/draw 需 `@larksuite/whiteboard-cli`。缺失时返回 `code: "whiteboard_cli_not_installed"`，跑 `npm i -g @larksuite/whiteboard-cli`（约 80MB native）。
8. **路径白名单**：`input_path` / `output_path` 必须在 `os.tmpdir()` 或 `/tmp` 下。

---

## 限制声明（API 现实）

- **无法程序化创建独立画板文件**：飞书开放平台 `drive.v1.file` 没有创建画板的 API；`importTask` 也不支持。新建画板的唯一程序入口是 `docx.documentBlockChildren.create` 嵌入到 docx。
- **无删除节点 API**：`whiteboardNode` 只有 create / create_plantuml / list 三个端点，不能 delete/update。要"撤销"只能重建画板。
- **PlantUML 不支持 update**：每次 `create_plantuml` 只生成新节点，不能改已有节点。

---

## References

`references/` —— 通用基础与路径：

- [`content.md`](references/content.md) ⭐ — **画什么比怎么画更重要**（视觉隐喻清单、内容充实度、视觉层级、配色克制）
- [`blueprint-style.md`](references/blueprint-style.md) ⭐ — 工程蓝图风格（分层封层、覆盖热力图、里程碑、指标金字塔、旅程泳道），配套 `templates/blueprint/*.svg`
- [`style.md`](references/style.md) — 配色色板（经典/商务/科技/清新/极简）+ 视觉一致性参数
- [`typography.md`](references/typography.md) — 字号 / 字色 / 行高 / 富文本混排 / 数字展示规约
- [`layout-patterns.md`](references/layout-patterns.md) — 通用布局原语（极坐标、等距、桑基、金字塔、同心圆、SVG 切割…）
- [`icons-lucide.md`](references/icons-lucide.md) — Lucide 图标库 CLI 集成（`<lucide />` 占位符 + `action: lucide`）
- [`dsl-schema.md`](references/dsl-schema.md) — `whiteboard-cli` DSL JSON 完整 schema、节点类型、TextRun、connector
- [`route-svg.md`](references/route-svg.md) ⭐ — **SVG 推荐主路径**（渐变、光晕、弧光、玻璃质感 + 飞书 svg-parser 实测支持矩阵）
- [`route-mermaid.md`](references/route-mermaid.md) — Mermaid 各图谱语法 + 飞书画板实测支持范围
- [`route-dsl.md`](references/route-dsl.md) — DSL JSON 路径（脚本生成 + 调试技巧）
- [`recipes.md`](references/recipes.md) — 端到端 workflow 范例（8 个 recipe）

`references/scenes/` —— 场景化 playbook（含可填空脚本模板）：

- [`scene-fishbone.md`](references/scenes/scene-fishbone.md) — 鱼骨图（4M1E 因果分析）
- [`scene-flywheel.md`](references/scenes/scene-flywheel.md) — 增长飞轮（自驱循环）
- [`scene-roadmap.md`](references/scenes/scene-roadmap.md) — 产品路线图（横向时间轴）
- [`scene-architecture.md`](references/scenes/scene-architecture.md) — 系统架构图（分层 + 模块依赖）
- [`scene-pyramid.md`](references/scenes/scene-pyramid.md) — 价值金字塔（层级递减）
- [`scene-funnel.md`](references/scenes/scene-funnel.md) — 漏斗图（转化分析）
- [`scene-organization.md`](references/scenes/scene-organization.md) — 组织架构图（树形层级）
- [`scene-layered-flow.md`](references/scenes/scene-layered-flow.md) — 分层泳道执行链路（工程系统、API 流程）
