---
name: feishu-meegle
description: |
  飞书项目（Meegle / Lark Project）操作 — MQL 查询、工作项 CRUD、子任务编排、工作流流转、视图、图表、评论、关联、附件等。
  通过 feishu-lark CLI 的 `feishu_meegle` tool 调用（spawn @lark-project/meegle）。

  当以下情况时使用：
  (1) 用户提到 Meegle / 飞书项目 / Lark Project / 工作项 / story / issue / bug / MQL
  (2) "查我的需求/待办"、"按字段过滤工作项"、"看我在 X 空间的任务"
  (3) "建一个需求 + N 个子任务 + 排期"
  (4) 任意 meegle 命令（comment / relation / view / chart / team / workhour / attachment / url 等）
---

# 飞书项目 (Meegle / Lark Project)

`feishu_meegle` 是 meegle CLI 的薄 wrapper —— **通用 passthrough** 设计，meegle 所有子命令都能调，不强行抄参数面。

## 执行前必读

- **节点 key 不要硬编 `started`** —— 每个空间/模板的初始节点 key 不同（PNSI=`started`，i18n-ecommerce 标准流程=`start`，仅评估流程模板=`started`）。建完 story 后跑 `workflow get-node` 看 `result.list[].basic.node_key`
- **子任务不能用 `workitem create`** —— 必须 `subtask update --action create`，否则报 `ProjectKey is empty or Count is zero`
- **`subtask update --schedule` 不落库** —— 排期必须分两步：先 subtask.update 建任务 → 再 `workitem update` 写 `sub_task_schedule` 字段。`task_creator_batch` 已自动处理
- **不传 `template` = 后端套默认全量模板**（i18n-ecommerce 是含法务的 11 节点版）。要精简就显式传 template option_id
- **工作项类型 mode 决定能不能挂子任务** —— node-flow（如 `story` / `issue`）才有节点；state-flow（如 `dailytask` / `tech_task`）没节点，subtask 挂不上
- **CLI 没有 delete** —— 测试遗留只能去 Meegle UI 手动删。建测试用 `[wrapper-test]` 前缀方便辨识
- **不同空间字段不一样** —— 国际化空间常用英文 api_name（`story` / `owner`），中文空间可能用中文 label。MQL 报 `attr label not found` → 改英文 key
- **MQL 不支持 `SELECT *`** —— 必须显式列字段。富文本字段（`description` / multi-text）返回体积爆炸，别选

---

## 5 个 action

| Action | 用途 |
|---|---|
| `call`（默认）| 透传任意 meegle 子命令；自动键名归一化 + projectKey/page-num 默认 |
| `inspect` | `meegle inspect <command>` 看任意命令的参数定义 |
| `task_creator_batch` | 编排：1×story + N×(subtask + workitem.update schedule) |
| `schedule_to_ms` | 纯本地：YYYY-MM-DD → CST 毫秒 + 现成的 sub_task_schedule field_value |
| `auth_status` | 安装/登录探测 |

`call` 的参数翻译：
- 键名 `pageNum` / `page_num` / `page-num` 自动统一为 kebab
- 数组 → 重复 flag（`fields:[a,b]` → `--fields a --fields b`）
- 嵌套对象 → JSON 序列化
- bool true → 开关 flag

自动注入默认：
- 缺 `project-key` 时走 defaults / env（auth/mywork/user/url/config 命令除外）
- `meta-fields` / `meta-roles` / `list-op-records` / `mywork.todo` 缺 `page-num` 时注入 `"1"`

---

## 快速索引

| 用户意图 | command | 关键 params |
|---|---|---|
| 查我的待办（跨空间） | `mywork todo` | `action: "todo"\|"done"\|"overdue"\|"this_week"` |
| 查当前用户 | `user me` | — |
| 解析空间名 → projectKey | `project search` | `project-key: <名字/simpleName>`（空字符串列最近） |
| MQL 查工作项 | `workitem query` | `project-key`, `mql` |
| 查单条工作项 | `workitem get` | `project-key`, `work-item-id`, `fields:["name",...]` |
| 批量查 | `workitem +batch-get` | `project-key`, `work-item-ids:[...]` (≤200) |
| 列工作项类型 | `workitem meta-types` | `project-key` |
| 查字段（含 option_id） | `workitem meta-fields` | `project-key`, `work-item-type` |
| 查角色 | `workitem meta-roles` | `project-key`, `work-item-type` |
| 建工作项 | `workitem create` | `project-key`, `work-item-type`, `fields:[...]` |
| 改工作项 | `workitem update` | `project-key`, `work-item-id`, `fields:[...]` |
| 建子任务 | `subtask update` | `action:"create"`, `project-key`, `work-item-id`, `node-id`, `fields:[...]` |
| 查节点 / transition | `workflow get-node` | `project-key`, `work-item-id` |
| 状态流转 | `workflow transition-state` | `project-key`, `work-item-id`, `target-state-key` |
| 评论 | `comment list` / `comment add` | `project-key`, `work-item-id`, `content`（add 用） |
| 视图 | `view search` / `view get` | `key-word`/`view-id` |
| URL 解析 | `url decode` | `url` |

不在表里的命令：`feishu_meegle({ action: "inspect", command: "<cmd>" })` 自查。

---

## CLI 调用示例

### 查我在某空间的待办

```ts
feishu_meegle({ command: "mywork todo", params: { action: "todo" } })
// → result.list[]，客户端按 project_key 过滤
```

### MQL 查询

```ts
feishu_meegle({
  command: "workitem query",
  params: {
    "project-key": "5f6330a7796d72a1ca2278c5",
    mql: "SELECT name, owner FROM `Global E-Commerce (国际化电商)`.`story` WHERE owner = current_login_user() LIMIT 20"
  }
})
```

翻页：`params: { "session-id": "<上次返回的 session_id>" }`，无需重传 mql。

### 元数据探查（建/改前必做）

```ts
feishu_meegle({ command: "workitem meta-types", params: { "project-key": "..." } })
feishu_meegle({ command: "workitem meta-fields", params: { "project-key": "...", "work-item-type": "story", "field-query": "owner" } })
feishu_meegle({ command: "workitem meta-roles",  params: { "project-key": "...", "work-item-type": "story" } })
```

### 建需求 + 任务 + 排期（推荐 task_creator_batch）

```ts
feishu_meegle({
  action: "task_creator_batch",
  projectKey: "5f6330a7796d72a1ca2278c5",
  story: {
    workItemType: "story",
    fields: [
      { field_key: "name", field_value: "新需求 X" },
      { field_key: "template", field_value: "95013" }   // 仅评估流程（3 节点，无法务）
    ]
  },
  subtasks: [
    { name: "任务 A", nodeKey: "started", scheduleStartDate: "2026-05-12", scheduleEndDate: "5/13" },
    { name: "任务 B", scheduleStartDate: "5/14", scheduleEndDate: "5/16" }   // nodeKey/assignee 走 defaults
  ]
})
```

任一步失败立刻返回**已建对象 ID**供清理（`partial_failure: true`）。

### 手动建子任务（不用 batch）

```ts
feishu_meegle({
  command: "subtask update",
  params: {
    action: "create",
    "project-key": "...",
    "work-item-id": "<story_id>",
    "node-id": "started",      // node_key，不是 node_uuid
    assignee: ["<userkey>"],
    fields: [{ field_key: "name", field_value: "..." }]
  }
})

// 排期单独走（subtask 内联不落库）
feishu_meegle({ action: "schedule_to_ms", scheduleStartDate: "2026-05-12", scheduleEndDate: "2026-05-13" })
// → { field_value: "[1778515200000,1778687999000]" }
feishu_meegle({
  command: "workitem update",
  params: {
    "project-key": "...",
    "work-item-id": "<subtask_id>",
    fields: [{ field_key: "sub_task_schedule", field_value: "[ms,ms]" }]
  }
})
```

### 长尾命令

```ts
// 自查参数
feishu_meegle({ action: "inspect", command: "workflow transition" })

// 调用
feishu_meegle({
  command: "workflow transition",
  params: { "project-key": "...", "work-item-id": "...", "transition-id": "...", fields: [...] }
})
```

---

## MQL 语法

```sql
SELECT <字段> FROM `空间名`.`工作项类型` WHERE <条件> ORDER BY <字段> [ASC|DESC] LIMIT <n>
```

- **空间名 / 类型名必须反引号**：`` FROM `空间名`.`story` ``
- 类型名可用 api_name（`story`/`issue`）或中文（`需求`/`缺陷`）。国际化空间用 api_name 更稳

### WHERE 速查

| 场景 | 写法 |
|---|---|
| 基本比较 | `WHERE priority = 'P0'` / `WHERE story_point > 5` |
| 时间范围 | `WHERE create_time >= '2026-01-01'` |
| 排期子字段 | `` WHERE `__排期字段_开始时间` >= '2026-05-01' ``（不能直接比较排期类型） |
| 角色字段 | `` `__开发负责人` = 'userkey_xxx' ``（`__` 前缀 + 角色名） |
| 数组字段 | `array_contains(labels, 'urgent')` / `any_match(assignees, x -> x = 'userkey_xxx')` —— 不能用 `=` |
| IN | `priority IN ('P0','P1')` |
| 模糊 | `name LIKE '%登录%'` |
| 当前用户 | `current_owner = current_login_user()` |
| 同名消歧 | `current_owner = '<id:7509072868295085608>'` |

---

## fields[] 编码规则（建/改通用）

`workitem create` / `workitem update` / `subtask update --action create` 的 `--fields` 是数组，每项一次：

| 字段类型 | 写法 |
|---|---|
| 单选 select（如 `priority`） | option_id 字符串，**不是** option_name。如 `"2"`（不是 `"P2"`） |
| 多选 multi_select | **`field_alias`** + 逗号分隔字符串。如 `{field_alias:"supported_apps", field_value:"4,2"}` |
| 特殊多选 multi_select（无可用 alias / 普通字符串报 illegal） | **`field_key`** + option 对象数组的 JSON 字符串。如 `{field_key:"field_e0bf59", field_value:"[{\"option_id\":\"Triangle-观测定位\"}]"}` |
| 级联 cascade（如 `business`） | **只传叶子 option_id**，后端补层级 |
| 工作项关联 work_item_related | **`field_alias`** + ID 字符串。如 `{field_alias:"PNSIproject", field_value:"3314348631"}` |
| bool | 字符串 `"true"` / `"false"` |
| schedule（如 `sub_task_schedule`） | `[start_ms,end_ms]` 字符串。用 `schedule_to_ms` 算 |
| text / 模板 template | option_id 字符串 |

例如 i18n-ecommerce 的 `项目集标签` 字段 `field_e0bf59`，直接传 `"Triangle-观测定位"` 或 `"[\"Triangle-观测定位\"]"` 会报 `field [field_e0bf59] is illegal`；改用 `field_value:"[{\"option_id\":\"Triangle-观测定位\"}]"`。

**调试**：backend 一次只报第一个错的字段；改一个跑一次。"invalid select option(s)" 错误会列出 possible values，复制 option_id 用就行。

---

## task_creator_batch 默认参数来源

按优先级：调用入参 > `./.feishu-lark/meego.json` > 环境变量。

| 参数 | JSON 字段 | 环境变量（主推 → 兼容） |
|---|---|---|
| `projectKey` | `projectKey` | `FEISHU_LARK_MEEGO_PROJECT_KEY` → `MEEGO_PROJECT_KEY` |
| 起始节点 nodeKey | `nodeKey` | `FEISHU_LARK_MEEGO_NODE_KEY` → `MEEGO_NODE_KEY` |
| 默认负责人 | `assigneeUserKey` | `FEISHU_LARK_MEEGO_ASSIGNEE_USER_KEY` |
| meegle host | — | `MEEGLE_HOST` / `FEISHU_LARK_MEEGO_HOST` |
| meegle token | — | `MEEGLE_USER_ACCESS_TOKEN` 等 |

`.feishu-lark/meego.json` 模板：

```json
{
  "projectKey": "<key>",
  "nodeKey": "started",
  "assigneeUserKey": "<userkey>",
  "businessOptionId": "<叶子option_id>",
  "projectWorkitemId": "<工作项 ID>",
  "templateId": "95013"
}
```

> 用户没说业务线 / 项目 / 模板时**用默认值，不要追问**。

---

## 工作流模板说明（建 story 必读）

- **不传 `template` = 后端套默认全量模板**（i18n-ecommerce 的标准流程含法务 + 11 节点）
- 各空间的可用模板列表用 `meta-fields field-keys=["template"]` 看
- i18n-ecommerce 验证过的精简模板：`95013 仅评估流程需求`（3 节点：需求提出 → 需求评估 → 结束，无法务无安全评审）
- **workflow 是 story 创建时凝固快照**。模板事后改了，已有 story 不重放
- 不少模板在选项列表里但 `Template is Disable` 报错。要先 dry-run 或建一条探针验证

---

## 常见错误

| 现象 | 原因 | 修复 |
|---|---|---|
| `attr label not found` | 字段名在该空间不存在 / 中英不匹配 | `meta-fields` 看真实可用字段，改 api_name |
| `Invalid nodeID started` 或类似 | 该空间/模板初始节点 key 不叫 `started` | `workflow get-node` 看 `result.list[].basic.node_key` |
| `Invalid nodeID node_xxx` | 传了 node_uuid 而不是 node_key | 改传 node_key 字符串 |
| `Current Template is Disable` | 模板被禁用 | 换其他模板，先用 `meta-fields field-keys=["template"]` 看可用 |
| `Workflow Not Found` | state-flow 类型用 workflow get-node | state-flow 类型用 `workflow list-state-transitions` |
| `ProjectKey is empty or Count is zero` 建 sub_task | 用了 `workitem create` 建子任务 | 改 `subtask update --action create` |
| sub_task 排期为空 | `subtask update` 内联了 schedule | 分两步：subtask.update → workitem.update 写 sub_task_schedule（task_creator_batch 已处理） |
| `invalid select option(s)` | cascade 传了父级 / select 传了 name | cascade 传叶子；select 改 option_id |
| 数组字段比较报错 | 用了 `=` | 改 `array_contains` / `any_match` |
| `required flag(s) "page-num" not set` | meta-* 必填 page-num | call action 已默认 `"1"`，或 params 显式传 |
| `meegle_cli_not_installed` | 缺 @lark-project/meegle | `npm i -g @lark-project/meegle` 或 `bun install` |
| token 过期 | meegle 未登录 / token 失效 | `auth_status` 探测，按提示 `meegle auth login --device-code` |
| stdout 截断 | 响应 >~80KB | `format: "ndjson"` 流式 / `select` 字段投影减体积 |

---

## 工作流建议

1. **`project search`** 拿 project_key（空间名 → key 消歧）
2. **`meta-types`** 列工作项类型，确认 `api_name` / `type_key`
3. **`meta-fields`** 看真实字段（不同空间字段不一样！）
4. **`meta-roles`** 看角色 key（写 `__角色名` MQL 用）
5. 拼装 MQL → `workitem query`；或建/改走 `workitem create` / `update`
6. 不确定参数 → `inspect` 查命令定义

## 最佳实践

1. **建之前先 `inspect` 或 `meta-fields`** —— 不要凭记忆拼参数
2. **空间不熟先 `project search`** —— 不要直接猜 projectKey
3. **国际化空间用 api_name** —— 英文 key 比中文 label 稳
4. **精简 SELECT** —— 只选必要字段
5. **批量建用 `task_creator_batch`** —— 别手写 N 次 subtask 调用
6. **排期用 `schedule_to_ms`** —— 不要 AI 自己算 CST 毫秒
7. **测试用 `[wrapper-test]` 前缀** —— meegle 没 delete，UI 删时容易找
