# Recipes — 端到端 Workflow 范例

> 把工具拼成完整的产出物。每个 recipe 都是经过测试的真实工作流。

## Recipe 1: 一句话生成可视化报告

**场景**：用户说"给我画一张电商 GMV 下滑根因分析"，要求飞书文档可读。

```bash
# 1. 自检（首次使用 / 怀疑环境问题时）
feishu-lark call feishu_whiteboard '{"action":"diagnose"}'

# 2. 想清楚画什么（参考 content.md）
#    主题：GMV 下滑 → 因果分析 → 鱼骨图（五维）
#    数据：流量端 / 转化端 / 商品端 / 服务端 / 运营端

# 3. 用脚本生成 DSL（鱼骨场景的模板）
mkdir -p /tmp/wb-demo
cp <scene-fishbone 模板> /tmp/wb-demo/fishbone.cjs
# 编辑 categories 数据
node /tmp/wb-demo/fishbone.cjs

# 4. 本地校验
feishu-lark call feishu_whiteboard '{"action":"check","input_path":"/tmp/wb-demo/fishbone.json","from":"dsl"}'
# 期望 errors: 0

# 5. 本地预览
feishu-lark call feishu_whiteboard '{"action":"render","input_path":"/tmp/wb-demo/fishbone.json","from":"dsl"}'
# Read 返回的 output_path 看 PNG

# 6. 起新文档（如果没有要写入的目标文档）
feishu-lark call feishu_create_doc '{
  "title": "GMV 下滑根因分析 · 2026 Q2",
  "markdown": "# 根因分析\n\n## §1 五维鱼骨\n\n下图展示 GMV 同比 -18% 的五个根因维度。"
}'
# 拿到 doc_id

# 7. 入文档
feishu-lark call feishu_whiteboard '{
  "action": "draw",
  "doc_id": "<doc_id>",
  "input_path": "/tmp/wb-demo/fishbone.json",
  "from": "dsl",
  "width": 1516,
  "height": 736
}'

# 8. 完成 → 返回 doc_url 给用户
```

## Recipe 2: 多图汇编报告

**场景**：年终复盘报告，需要 3 张图：增长飞轮 + 业务漏斗 + 路线图。

```bash
# 1. 起文档（先写好章节骨架）
feishu-lark call feishu_create_doc '{
  "title": "2026 业务复盘 · Q1-Q3",
  "markdown": "# 业务复盘\n\n## §1 增长飞轮\n\n四阶段闭环现状。\n\n## §2 转化漏斗\n\n月度对比分析。\n\n## §3 Q4 路线图\n\n下一阶段重点。"
}'
# doc_id: AbCdEf...

# 2. 依次生成 3 个 DSL JSON
node /tmp/wb-demo/flywheel.cjs    # → flywheel.json
node /tmp/wb-demo/funnel.cjs      # → funnel.json
node /tmp/wb-demo/roadmap.cjs     # → roadmap.json

# 3. 全部 check 一遍
for f in flywheel funnel roadmap; do
  feishu-lark call feishu_whiteboard "{\"action\":\"check\",\"input_path\":\"/tmp/wb-demo/$f.json\",\"from\":\"dsl\"}"
done

# 4. 依次 draw 到同一文档
feishu-lark call feishu_whiteboard '{"action":"draw","doc_id":"AbCdEf...","input_path":"/tmp/wb-demo/flywheel.json","from":"dsl","width":1200,"height":920}'
feishu-lark call feishu_whiteboard '{"action":"draw","doc_id":"AbCdEf...","input_path":"/tmp/wb-demo/funnel.json","from":"dsl","width":1500,"height":800}'
feishu-lark call feishu_whiteboard '{"action":"draw","doc_id":"AbCdEf...","input_path":"/tmp/wb-demo/roadmap.json","from":"dsl","width":1600,"height":700}'

# 5. 完成 → 3 张画板各自独立，不会互相重叠
```

> **关键**：多张图必须用多次 `draw` —— 每次 `draw` 是新画板。不要往同一画板反复 `add_nodes`，会堆叠。

## Recipe 3: 暗夜主题信息图（SVG 渐变光晕）

**场景**：技术 keynote 配图，要"赛博朋克"科技感。

```bash
# 1. 创目录
mkdir -p /tmp/wb-demo

# 2. 写 SVG（用渐变 + 径向光晕 + Lucide 图标）
cat > /tmp/wb-demo/keynote.svg <<'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#0F172A"/>
      <stop offset="1" stop-color="#1E293B"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="50%" r="50%">
      <stop offset="0" stop-color="#38BDF8" stop-opacity="0.95"/>
      <stop offset="1" stop-color="#38BDF8" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect x="0" y="0" width="1600" height="900" fill="url(#bg)"/>
  <circle cx="800" cy="450" r="400" fill="url(#glow)"/>
  <text x="800" y="430" font-size="60" text-anchor="middle" fill="#F1F5F9" font-weight="800">
    NEXT GENERATION
  </text>
  <text x="800" y="490" font-size="20" text-anchor="middle" fill="#94A3B8">
    AI · Engineering · Design
  </text>
  <lucide name="sparkles" x="780" y="540" size="40" stroke="#38BDF8"/>
</svg>
EOF

# 3. 验证 + 预览（深色背景 svg 配 check 抓不到 layout 问题，但抓得到 overlap）
feishu-lark call feishu_whiteboard '{"action":"check","input_path":"/tmp/wb-demo/keynote.svg","from":"svg"}'
feishu-lark call feishu_whiteboard '{"action":"render","input_path":"/tmp/wb-demo/keynote.svg"}'

# 4. 入文档
feishu-lark call feishu_whiteboard '{
  "action": "draw",
  "doc_id": "<doc_id>",
  "input_path": "/tmp/wb-demo/keynote.svg",
  "width": 1600,
  "height": 900
}'
```

## Recipe 4: 修复一张老画板（用 list_nodes + add_nodes）

**场景**：飞书画板上有一张同事手画的架构图，要补一些新节点 + 改主题。

```bash
# 1. 拿到 whiteboard_id（从飞书 UI 复制 token 或者 docx?block= URL）
WB="MTlaw76kYhW5AfbaKJ4cCgcpnrh"

# 2. 看现状
feishu-lark call feishu_whiteboard "{\"action\":\"list_nodes\",\"whiteboard\":\"$WB\"}" | jq '.node_count, .nodes[0:3]'

# 3. 改主题
feishu-lark call feishu_whiteboard "{\"action\":\"update_theme\",\"whiteboard\":\"$WB\",\"theme\":\"vibrant_color\"}"

# 4. 准备新节点 SVG（用 lucide 占位符）
cat > /tmp/wb-demo/append.svg <<'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 200">
  <rect x="40" y="40" width="200" height="120" rx="10" fill="#F0F4FC" stroke="#5178C6" stroke-width="2"/>
  <lucide name="zap" x="56" y="56" size="28" stroke="#5178C6"/>
  <text x="92" y="76" font-size="16" font-weight="700" fill="#0F172A">缓存层</text>
  <text x="56" y="106" font-size="12" fill="#646A73">Redis · Upstash KV</text>
  <text x="56" y="124" font-size="12" fill="#646A73">unstable_cache</text>
</svg>
EOF

# 5. 追加节点（务必 auto_below 避免与现有内容重叠）
feishu-lark call feishu_whiteboard "{
  \"action\": \"add_nodes\",
  \"whiteboard\": \"$WB\",
  \"input_path\": \"/tmp/wb-demo/append.svg\",
  \"auto_below\": true
}"
# 返回 offset_applied 显示自动平移到 y=??
```

## Recipe 5: 时序图（最快路径 — Mermaid）

**场景**：API 设计文档需要画时序图，懒得算坐标。

```bash
# 1. 直接 mermaid
feishu-lark call feishu_whiteboard '{
  "action": "draw",
  "doc_id": "<doc_id>",
  "from": "mermaid",
  "content": "sequenceDiagram\n  participant U as User\n  participant API\n  participant DB\n  U->>API: POST /order\n  activate API\n  API->>DB: INSERT\n  DB-->>API: id\n  API-->>U: 201 Created\n  deactivate API"
}'
# whiteboard-cli 自动 dagre 布局 → 飞书节点 → 入文档。零坐标计算。
```

## Recipe 6: PlantUML（飞书原生，无依赖）

**场景**：UML 类图 / 时序图，想用 PlantUML 语法（比 mermaid 表达力更强）。

```bash
# 1. 先建画板（draw 一个空的或拿现有 wb_id）
RES=$(feishu-lark call feishu_whiteboard '{"action":"create_in_doc","doc_id":"<doc_id>"}')
WB=$(echo "$RES" | jq -r '.whiteboard_id')

# 2. PlantUML 直出
feishu-lark call feishu_whiteboard "{
  \"action\": \"create_plantuml\",
  \"whiteboard\": \"$WB\",
  \"plant_uml_code\": \"@startuml\nclass User {\n  +id\n  +email\n}\nclass Order\nUser '1' -- '*' Order\n@enduml\"
}"
# 不依赖 whiteboard-cli，纯飞书 API
```

## Recipe 7: 仿样图重画（参考用户已有图）

**场景**：用户给一张其他文档的画板截图，说"画一张这样的"。

```bash
# 1. 看截图，识别：
#    - 几个泳道？什么色系？
#    - 每个步骤的 icon + 文字结构？
#    - 跨层箭头的颜色编码？
#    - 嵌套子流程区在哪一层？

# 2. 对照 scenes/scene-layered-flow.md 的骨架代码

# 3. 写 SVG（多用 <lucide /> 占位符，少手画图标）

# 4. check + render + 对比截图 → 修 → 再 render
feishu-lark call feishu_whiteboard '{"action":"check","input_path":"/tmp/wb-demo/clone.svg","from":"svg"}'
feishu-lark call feishu_whiteboard '{"action":"render","input_path":"/tmp/wb-demo/clone.svg"}'
# 反复 1-2 轮调整后入文档

feishu-lark call feishu_whiteboard '{
  "action": "draw",
  "doc_id": "<doc_id>",
  "input_path": "/tmp/wb-demo/clone.svg",
  "width": 1800,
  "height": 1300
}'
```

## Recipe 8: 多输入格式混用

**场景**：一张图里既有自由 SVG 设计，又想嵌入 mermaid 时序图。

> **不支持**。一张画板（一次 draw）只能用一种 `from`。
> **变通方案**：起两张相邻的画板：
> ```bash
> # 画板 A：SVG 主图
> feishu_whiteboard draw {doc_id, input_path: ".svg"}
> # 画板 B：紧跟其后的 mermaid 时序图
> feishu_whiteboard draw {doc_id, from: "mermaid", content: "..."}
> ```

## 通用建议

1. **永远先 diagnose**：换机器 / 长时间没用 / 报错时先跑 `action: diagnose`
2. **永远先 check 再 draw**：本地校验 0 issues 再上飞书
3. **永远先 render 看 PNG**：眼睛是最好的 linter
4. **改脚本不改 JSON**：可重复、可追溯
5. **多图用多次 draw**：每张图独立画板，不要 add_nodes 堆叠
6. **width/height 必须等于 canvas**：传错就裁切
7. **用 Lucide 不手画**：`<lucide />` 占位符瞬间专业一档

## 顺序速查

| 阶段 | Action |
|---|---|
| 准备 | `diagnose` |
| 校验 | `check` |
| 预览 | `render` |
| 落地（推荐主用）| `draw` |
| 追加 | `add_nodes` + `auto_below: true` |
| 反向读 | `list_nodes` |
| 调主题 | `update_theme` |
| PlantUML 快路径 | `create_plantuml` |
| 取图标 | `lucide`（或在 SVG 里用 `<lucide />` 占位符）|
