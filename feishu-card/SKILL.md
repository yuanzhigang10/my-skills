---
name: feishu-card
description: |
  构造并发送飞书/Lark V2.0 交互式消息卡片（interactive card）。
  优先通过 feishu-lark CLI 调用 `feishu_card` 渲染、校验、发送或回复卡片；只有完全手工调试时才退回 `feishu_im_user_message`。

  当以下情况时使用：
  (1) 用户明确要求"飞书卡片"、"Lark card"、"interactive card"、"卡片消息"、"发卡片"
  (2) 需要发送结构化通知、告警、审批、周报、发版报告、数据看板、文章摘要
  (3) 需要把 AI/bot 的长回答、检索结果、代码证据或排障结论整理成更好读的卡片
  (4) 消息包含多字段、多链接、状态标签、按钮、折叠详情、图表或表格
  (5) 用户说"美化一下消息"、"发个通知/报告/告警到群里"，且内容不是单句纯文本
---

# 飞书 V2 交互式卡片

## 执行前必读

- 本 skill 负责构造卡片 JSON，并优先用 `feishu_card` 渲染、校验、发送或回复；`feishu_im_user_message` 只作为手工兜底。
- 面向群 bot 的排查场景优先使用 `--auth-mode bot` 或 `FEISHU_AUTH_MODE=bot`，避免读取、恢复或申请人的授权。
- 需要完整排查报告时，先用 `feishu_create_doc` 的 `as: "bot"` 创建飞书文档，再把文档 URL 放入卡片 `card_link`、正文 `<link>` 和主按钮。
- bot 创建排查文档会默认应用分享策略：L2 策略声明、租户内收到链接的人可编辑、可编辑协作者可管理。需要收紧或放宽时传 `permission_policy`。
- 当前 `feishu_im_user_message` 只支持 `receive_id_type: "open_id" | "chat_id"`；bot 模式要求已知 `open_id` / `chat_id`。如果用户只给邮箱、姓名或群名，需要先切回 user 模式使用搜索工具解析，或请用户提供明确 ID。
- 发送前必须确认接收对象和最终内容，除非用户在同一句中已经明确给出收件人/群和要发送的内容。
- 卡片使用 V2 schema：顶层必须有 `"schema": "2.0"`，正文必须放在 `body.elements`。
- 使用 `feishu_card` 时可传 `source.raw/preset/compose` 或 `bot_answer`；手工退回 `feishu_im_user_message` 时，`content` 必须是卡片 JSON 的字符串值，不要包成 `{ "card": ... }`。
- 不要编造 `img_key`。卡片图片支持自动上传：`img` 元素可写 `img_url`（http/https URL）或 `img_path`（本地路径，限 cwd/临时目录），`img_key` 直接写 URL 或路径也可以，markdown 里的 `![alt](http URL)` 同样支持；`feishu_card` 发送时会统一上传并替换成真实 `img_key`。也可先用 `feishu_im_media_upload` 单独上传拿 key。
- 默认用 `open_url` 按钮。只有用户明确已有卡片回调服务时，才使用 `callback` behavior，并确认回调 payload。

## 快速选型

| 用户意图 | 推荐模板 | 主色 |
| --- | --- | --- |
| 通知、公告、信息同步 | `templates/notification.json` | `blue` |
| 成功、完成、发布、交付 | `templates/success-report.json` | `green` |
| 告警、故障、错误、风险 | `templates/alert.json` | `red` / `carmine` |
| 审批、待办、确认 | `templates/approval.json` | `orange` |
| 数据报表、指标、dashboard | `templates/data-dashboard.json` | `purple` / `indigo` |
| AI/bot 回答、代码检索结论、知识问答 | `templates/bot-answer.json` | `wathet` / `blue` |

不确定时用 `notification.json`。如果只是单句消息且没有结构，改用 `msg_type: "text"`，不用卡片。

## 最小骨架

```json
{
  "schema": "2.0",
  "config": {
    "update_multi": true,
    "enable_forward": true,
    "width_mode": "fill"
  },
  "header": {
    "template": "blue",
    "title": { "tag": "plain_text", "content": "标题" },
    "subtitle": { "tag": "plain_text", "content": "可选副标题" }
  },
  "body": {
    "direction": "vertical",
    "vertical_spacing": "medium",
    "elements": [
      { "tag": "markdown", "content": "**核心结论**\n\n正文内容" }
    ]
  }
}
```

## 工作流

优先使用一等工具 `feishu_card`，只有需要手工调试模板时才直接调用 `feishu_im_user_message`。

1. 识别场景并选择模板；按需读取 `references/design.md`、`references/components.md` 和 `templates/manifest.json`。
2. 生成卡片时先走 dry-run：`feishu-lark --auth-mode bot call feishu_card '{"action":"render_bot_answer","bot_answer":{...},"dry_run":true}'`。
3. 发送前必须通过 `feishu_card validate` 或 `send_bot_answer` 内置校验：不得残留占位符、不得使用 V1 字段、按钮 URL 必须真实。
4. 排查类卡片优先用 `send_bot_answer` / `reply_bot_answer`，由工具自动创建 bot 文档、生成卡片、校验并发送。
5. 只有需要完全自定义 JSON 时才手动发送。CLI 推荐用 Node 组装 payload，避免 shell 转义破坏 JSON：

```bash
payload="$(node -e 'const fs=require("fs"); const card=JSON.stringify(JSON.parse(fs.readFileSync("/tmp/topic-card.json","utf8"))); console.log(JSON.stringify({action:"send",send_as:"bot",receive_id_type:"chat_id",receive_id:"oc_xxx",msg_type:"interactive",content:card}))')"
feishu-lark call feishu_im_user_message "$payload"
```

回复某条消息：

```bash
payload="$(node -e 'const fs=require("fs"); const card=JSON.stringify(JSON.parse(fs.readFileSync("/tmp/topic-card.json","utf8"))); console.log(JSON.stringify({action:"reply",send_as:"bot",message_id:"om_xxx",msg_type:"interactive",content:card,reply_in_thread:true}))')"
feishu-lark call feishu_im_user_message "$payload"
```

MCP 直接调用时，传：

```json
{
  "action": "send",
  "send_as": "bot",
  "receive_id_type": "chat_id",
  "receive_id": "oc_xxx",
  "msg_type": "interactive",
  "content": "<JSON.stringify(card)>"
}
```

## 组件选择

| 需求 | 组件 |
| --- | --- |
| 富文本、列表、链接、行内标签、@人 | `markdown` |
| 2x2 关键字段、状态摘要 | `div.fields` |
| 章节分隔 | `hr` |
| 两列/三列布局、按钮组 | `column_set` |
| 次要详情、长清单、技术细节 | `collapsible_panel` |
| 跳转或回调 | `button` |
| 柱状图、折线图、饼图、漏斗图 | `chart` |
| 截图、示意图、海报 | `img`（`img_key` / `img_url` / `img_path`，URL 和路径发送时自动上传） |
| 简单明细 | markdown 表格；复杂明细可用 `table` |

## 图片多形式支持

图片不需要预先有 `img_key`，以下形式在发送前都会自动上传替换（相同来源只上传一次）：

| 形式 | 写法 | 说明 |
| --- | --- | --- |
| img 元素 + URL | `{"tag":"img","img_url":"https://...","alt":{...}}` | 自动下载后上传 |
| img 元素 + 本地路径 | `{"tag":"img","img_path":"/tmp/shot.png","alt":{...}}` | 限 cwd 或系统临时目录内 |
| img_key 直接写 URL/路径 | `{"tag":"img","img_key":"https://..."}` | 兼容写法，同样自动解析 |
| markdown 图片 | `![截图](https://...)` | 仅支持 http(s) URL |
| bot_answer 快捷插图 | `"images":[{"src":"URL或路径","alt":"说明","title":"可选标题"}]` | 最多 5 张，渲染在字段区之后 |
| 独立上传 | `feishu_im_media_upload {"media_type":"image","source":"URL或路径"}` | 返回 `img_key`，适合复用或手工链路 |

规则：

- 图片上限 10MB（JPEG/PNG/WEBP/GIF/TIFF/BMP/ICO），文件上限 30MB。
- `validate` / `render_bot_answer` / `dry_run` 默认不上传，只输出 warning 提示；显式传 `resolve_images: true` 可提前上传拿真实 key。
- 发送类 action（send / reply / send_bot_answer / reply_bot_answer）默认自动解析；传 `resolve_images: false` 且残留未解析图片会被校验阻断。
- `feishu_im_user_message` 也支持：快捷参数 `image` / `file`（key/URL/路径，自动推断 msg_type），或 content 里写 `image_url` / `image_path` / `file_url` / `file_path`。
- 上传身份与发送身份一致（卡片走 bot）；仍然禁止编造 `img_key`。

## AI/bot 咨询与排查卡片

当用户说"把 bot 输出放到卡片里"或群里出现长 Markdown 答案时，优先使用 `templates/bot-answer.json`。它不是只服务接口排查，而是一个类型化咨询卡片。

咨询类型：

| `answer_type` | 适用场景 | 默认矩阵列 | 默认追问方向 |
| --- | --- | --- | --- |
| `api_diagnosis` | 接口、RPC、入参、返回、调用链 | 场景 / 接口/方法 / 证据 / 注意 | 入参返回、调用文件、相关场景 |
| `display_issue` | 页面展示、样式、错位、文案、截图、设计稿 | 页面/模块 / 现象 / 原因/依据 / 处理 | 影响范围、截图录屏、设计稿/验收口径 |
| `interaction_issue` | 点击、流程、跳转、弹窗、输入、提交、空状态 | 操作/流程 / 问题 / 建议 / 验证 | 预期流程、异常分支、埋点/权限 |
| `permission_issue` | 无权限、分享、密级、角色、链接访问 | 对象 / 权限状态 / 依据 / 处理 | 角色范围、当前权限、读写管理策略 |
| `data_issue` | 指标、报表、口径、同步、前后端数据不一致 | 指标/字段 / 结论 / 口径/来源 / 风险 | 统计口径、影响范围、差异来源 |
| `git_diff_review` | git diff、MR/PR、patch、变更评审 | 文件/范围 / 发现 / 依据 / 建议 | 高风险问题、修复 patch、测试缺口 |
| `code_review` | 代码评审、CR、模块质量审查 | 文件/模块 / 问题 / 原因 / 建议 | 高风险问题、修改建议、回归清单 |
| `howto` | 操作咨询、配置教程、步骤说明 | 步骤 / 做法 / 依据 / 注意 | 前置配置、完整示例、失败提示 |
| `generic` | 其它咨询 | 主题 / 结论 / 依据 / 注意 | 限制条件、具体例子、下一步验证 |

处理原则：

- 首屏必须回答问题：用 1-3 句话写"一句话结论"，不要让用户先读证据。
- 卡片只做摘要和导航；完整证据、代码片段、长表格、白板/妙笔说明写入飞书文档。
- 文档链接必须是一等入口：顶层 `card_link`、正文 `<link>`、主按钮 `open_url` 三处都放真实 `doc_url`。
- 如果工具可用，排查文档必须用 `feishu_create_doc {"as":"bot"}` 创建，卡片 footer 标注 `文档创建身份：bot`。
- 根据 `answer_type` 选择矩阵列名和默认追问；agent 可用 `primary_label`、`secondary_label`、`evidence_columns`、`steps_title` 覆写。
- 把多个候选答案按该咨询类型的"场景/结论/依据/风险"拆成表格或 2x2 字段；不要只给一段代码块。
- 置信度只写来自证据的判断：`高`、`中`、`低`、`需人工复核`，并说明原因。
- 搜索关键词、命中文件、失败分支、日志、长代码、截图说明全部放进文档；卡片折叠面板只保留精简分析依据和处理步骤。
- 不要在卡片里批判、评价或影射前一个 agent / bot；语气只面向用户解决问题。
- 继续追问优先做成按钮。已有卡片回调服务时可用 `callback`；没有回调服务时用 `follow_up_mode: "open_url"` / `"sidebar"` 跳到真实继续提问入口，仍没有真实入口才降级成文本。
- diff、review、日志、看板这类重详情页优先传 `side_panel_url`，工具会在 `pc_url` 生成 Feishu applink：`client/web_url/open?mode=sidebar-semi&url=...`，PC 按钮在右侧栏打开详情，移动端保留原始 URL。`git_diff_review` / `code_review` 严格模式必须提供真实详情入口：`side_panel_url`、`detail_url`、`diff_url` 或 `detail_url_template`；`doc_url` 只是补充文档入口，不算真实 diff/review 入口。
- 技术问答默认保留"下一步验证"，告诉用户应该用哪个文件、接口、页面、设计稿、权限或数据口径继续确认。

推荐顺序：

1. 总结问题和结论，生成飞书文档 Markdown。
2. 调用 `feishu_card` 的 `send_bot_answer` 或 `reply_bot_answer`，传 `bot_answer.doc_markdown`。工具会用 bot 身份创建文档、填入 `doc_url`、校验卡片并发送。
3. 如果已有文档，直接传 `bot_answer.doc_url` / `doc_title`，工具不会重复建文档。
4. 如果工具不可用，才退回到 `feishu_create_doc {"as":"bot"}` + `feishu_im_user_message {"send_as":"bot"}` 的手工链路。

自由组合模式：

| `source.type` | 用法 |
| --- | --- |
| `raw` | 直接传完整 V2 card 到 `source.card`，仍复用发送、回复和 strict validate |
| `preset` | 传 `source.preset:"bot_answer"` + `source.bot_answer`，等价于旧 `bot_answer` 快捷入口 |
| `compose` | 基于 `source.card` 或 `source.bot_answer`，用 `slots` / `body_elements` / `insert_before` / `insert_after` / `replace` 自定义结构 |

优先用 `compose` 解决特殊场景，不要为了自由度绕回固定模板复制粘贴。常见做法：`slots.summary` 换首屏结论，`slots.fields` 换 2x2 字段，`slots.details` 加自定义折叠面板，`replace` 用 element_id 替换任意组件。

默认文档权限：

| 字段 | 默认值 | 含义 |
| --- | --- | --- |
| `sensitivityLevel` | `L2` | 文档策略声明；租户实际密级标签由飞书文档安全策略决定 |
| `linkShareEntity` | `tenant_editable` | 租户内收到链接的人可编辑 |
| `securityEntity` | `anyone_can_edit` | 可编辑者可调整安全设置 |
| `manageCollaboratorEntity` | `collaborator_can_edit` | 可编辑协作者可管理协作者 |
| `shareEntity` | `same_tenant` | 允许租户内分享 |

已有文档点不开时，使用 `feishu_drive_permission {"action":"apply","token":"docx_url_or_token"}` 修复公开权限。

继续追问按钮：

| 字段 | 用法 |
| --- | --- |
| `follow_up_prompts` | 简单模式，工具会自动取前 3 条；未启用回调且无 `follow_up_base_url` 时会降级为文本 |
| `follow_up_actions` | 精细模式，自定义按钮文案、prompt、callback value 或跳转 URL；`mode: "sidebar"` 会把 URL 包成右侧栏 applink；agent 可覆写、增删、排序 |
| `follow_up_input` | 自由输入框配置，可设 placeholder、submit_text、max_length、rows、callback value |
| `follow_up_mode` | `callback` 需要回调服务；`open_url` 用真实 URL；`sidebar` 用右侧栏 applink；`input` 只展示输入框；`hybrid` 按钮 + 输入框；`text` 降级为折叠文本 |
| `follow_up_base_url` | `open_url` / `sidebar` 模式下自动附加 `query`、`prompt`、`topic`、`doc_url`、`review_id`、`diff_url`、`detail_url` 参数；不要把含敏感临时 token 的 URL 放进追问服务 |
| `side_panel_url` | 卡片主操作区的详情页入口，适合 diff/review/日志/看板；默认 `mode=sidebar-semi` |
| `side_panel_options` | 可配置 `mode`、`max_width`、`reload`、`applink_domain`，默认域名 `https://applink.feishu.cn` |
| `doc_label` / `doc_button_text` | 覆写正文详情入口标签和主按钮文案；当 `doc_url` 实际指向妙笔、Review 页面或系统详情页时必须改成准确文案 |

启用 `botRuntime.cardCallback.enabled=true` 或单次请求 `callback.enabled=true` 后，默认 callback payload：

```json
{
  "action": "feishu_card.follow_up",
  "topic": "gs-pda · 接口排查",
  "question": "原问题",
  "prompt": "这个接口的入参和返回字段是什么？",
  "doc_url": "https://...",
  "review_id": "review_123",
  "diff_url": "https://...",
  "detail_url": "https://..."
}
```

bot 后端收到该 payload 后，应把 `prompt` 作为继续追问输入，带上原始 `topic/question/doc_url/review_id` 上下文，生成新的 bot-answer 卡片并以 thread reply 或 card update 方式返回。

输入框提交 payload：

```json
{
  "action": "feishu_card.follow_up_input",
  "topic": "gs-pda · 接口排查",
  "question": "原问题",
  "doc_url": "https://...",
  "review_id": "review_123",
  "diff_url": "https://...",
  "detail_url": "https://...",
  "input_name": "follow_up_query"
}
```

用户输入值会出现在飞书卡片回调的 `action.form_value.follow_up_query`。后端应优先读取这个值作为继续追问内容；如果同时存在快捷按钮和输入框，输入框用于临场补充问题，快捷按钮用于高频路径。

右侧栏详情按钮示例：

```json
{
  "side_panel_url": "https://example.com/detail?id=123",
  "side_panel_button_text": "右侧看 Diff",
  "side_panel_options": {
    "mode": "sidebar-semi",
    "max_width": 800,
    "reload": false
  }
}
```

实际按钮会保留 `default_url/ios_url/android_url` 为原始地址，并把 `pc_url` 变成：

```text
https://applink.feishu.cn/client/web_url/open?mode=sidebar-semi&url=https%3A%2F%2Fexample.com%2Fdetail%3Fid%3D123&max_width=800&reload=false
```

`send_bot_answer` 示例：

```json
{
  "action": "send_bot_answer",
  "receive_id_type": "chat_id",
  "receive_id": "oc_xxx",
  "bot_answer": {
    "topic": "gs-pda · 接口排查",
    "answer_type": "api_diagnosis",
    "question": "盘点页面获取正在进行的盘点任务是哪个接口",
    "short_answer": "页面实时状态优先看 GetCurUserInvCheckOrder；任务列表/领取场景看 GetCurInvCheckTaskPDA。",
    "primary_answer": "managementService.GetCurUserInvCheckOrder",
    "secondary_answer": "managementService.GetCurInvCheckTaskPDA",
    "confidence": "高",
    "next_step": "核对页面入口和调用文件",
    "doc_markdown": "# 完整排查报告\n\n...",
    "side_panel_url": "https://example.com/detail?id=123",
    "side_panel_button_text": "右侧看调用链",
    "follow_up_mode": "hybrid",
    "follow_up_actions": [
      {
        "text": "查入参返回",
        "prompt": "这个接口的入参和返回字段是什么？"
      },
      {
        "text": "定位调用文件",
        "prompt": "页面是在哪个文件调用它的？"
      },
      {
        "text": "找相关场景",
        "prompt": "有没有另一个场景会调用不同接口？"
      }
    ],
    "follow_up_input": {
      "placeholder": "补充你的问题，例如：顺便把调用链和入参也列一下",
      "submit_text": "发送追问",
      "max_length": 500,
      "rows": 3
    },
    "permission_policy": {
      "sensitivityLevel": "L2",
      "linkShareEntity": "tenant_editable",
      "manageCollaboratorEntity": "collaborator_can_edit"
    },
    "evidence": [
      {
        "scene": "页面实时状态",
        "answer": "GetCurUserInvCheckOrder",
        "evidence": "slice.tsx 初始化和状态恢复链路",
        "risk": "仅适用于当前用户正在进行的任务"
      }
    ]
  }
}
```

展示/交互咨询示例只需要换 `answer_type` 和字段语义：

```json
{
  "topic": "库存看板 · 展示问题",
  "answer_type": "display_issue",
  "question": "表格金额列在英文环境下被截断怎么办",
  "short_answer": "优先按列宽自适应和 tooltip 兜底处理，同时确认英文长文案和金额格式不会挤压操作列。",
  "primary_answer": "列宽策略缺少长文本和本地化金额的兜底",
  "secondary_answer": "补充 min/max width、tooltip、移动端折行规则",
  "next_step": "用英文环境、最大金额和窄屏分别复测",
  "evidence": [
    { "scene": "金额列", "answer": "英文环境截断", "evidence": "长货币符号 + 千分位占用更宽", "risk": "操作列不能被挤压" }
  ]
}
```

## 校验闭环

完整卡片必须通过这些检查：

1. JSON 语法合法，`content` 是卡片 JSON 的字符串，不包 `{ "card": ... }`。
2. 顶层 `schema` 为 `"2.0"`，正文在 `body.elements`。
3. 禁止顶层 `elements`、`action`、`note`、`wide_screen_mode`、`compact_width`、`i18n_elements`。
4. 禁止残留 `__[A-Z0-9_]+__` 占位符；字段契约见 `templates/manifest.json`。
5. `card_link` 必须在顶层；按钮 `open_url.default_url` 必须是真实 `http(s)` URL。
6. 卡片小于 30KB、元素少于 200、可见主按钮不超过 3 个。
7. `table` 不嵌套在 `column_set` / `collapsible_panel` / `form` 内。
8. 无回调服务时禁止 callback 按钮；图片来源必须可解析：真实 `img_key`、http(s) URL 或本地路径（发送时自动上传），禁止编造 key。
9. `git_diff_review` / `code_review` 必须有真实详情入口，不能只给 `doc_url`。

## 失败矩阵

| 失败 | 处理 |
| --- | --- |
| bot 建文档失败 | 不发送半成品卡片；先返回错误和缺失权限/空间信息 |
| bot 不在群或无 `im:message` | 提示邀请 bot 入群或开通应用权限，不改用用户身份绕过 |
| 目标只有群名/邮箱 | bot 模式要求已知 `chat_id` / `open_id`；需要用户提供 ID 或切回 user 模式解析 |
| 卡片校验失败 | 修正 JSON/占位符/URL/组件嵌套后再发，不降级发送错误卡片 |
| 卡片过长 | 把日志、长代码、长表格放进 bot 文档，卡片只保留摘要和入口 |
| 飞书拒绝卡片结构 | 用 `feishu_card validate` 定位常见 V1 字段和 `card_link` 位置 |

更完整的字段和坑点见：

- `references/components.md`：组件字段、嵌套规则、颜色/字号
- `references/design.md`：配色、布局节奏、信息层级
- `references/v2-migration.md`：v1 到 v2 迁移与禁用字段
- `references/vchart.md`：常见 `chart_spec` 骨架

## 设计守则

- 先写结论，再写字段，再写详情，最后放按钮和灰色来源信息。
- 一张卡片只保留一个主色，强调色不超过 2 个；备注用 `<font color='grey'>...</font>`。
- 4 个以上按钮不要平铺；最多 3 个主操作，更多操作改成链接列表或折叠详情。
- 超过 200 字的次要说明放进 `collapsible_panel`。
- 图表不要超过 5 个；移动端优先选 `bar`、`line`、`pie`，少用复杂组合图。

## 常见错误

| 错误 | 修正 |
| --- | --- |
| `content format error` | 先用 `python -m json.tool` 校验卡片文件，再确保 `content` 是 JSON 字符串 |
| 卡片显示"请升级客户端" | 确认客户端支持 V2；读取历史消息时使用 raw/user card content |
| `invalid element` | 删除 v1 字段，检查 `body.elements` 和组件嵌套 |
| 图片不显示 | 经 `feishu_card` 发送时 URL/本地路径会自动上传替换；手工绕过 `feishu_card` 直发时 `img_key` 必须是真实飞书 key，可先用 `feishu_im_media_upload` 上传 |
| 发不出去 | 检查 bot 是否在目标群、应用是否有 `im:message` 权限 |
