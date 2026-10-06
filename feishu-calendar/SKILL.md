---
name: feishu-calendar
description: |
  飞书日历与日程管理。包含日历管理、日程管理、参会人管理、忙闲查询。
  通过 feishu-lark CLI 调用。
---

# 飞书日历管理 (feishu-calendar)

## 执行前必读

- 时区固定：Asia/Shanghai（UTC+8）
- 时间格式：ISO 8601 / RFC 3339（带时区），例如 `2026-02-25T14:00:00+08:00`
- create 最小必填：summary, start_time, end_time
- user_open_id 强烈建议：确保用户能看到日程并出现在参会人列表中
- ID 格式约定：用户 `ou_...`，群 `oc_...`，会议室 `omm_...`

---

## 快速索引：意图 → 工具 → 必填参数

| 用户意图 | 工具 | action | 必填参数 | 常用可选 |
|---------|------|--------|---------|---------|
| 创建会议 | feishu_calendar_event | create | summary, start_time, end_time | user_open_id, attendees, description |
| 查某时间段日程 | feishu_calendar_event | list | start_time, end_time | - |
| 改日程时间 | feishu_calendar_event | patch | event_id, start_time/end_time | summary |
| 搜关键词找会 | feishu_calendar_event | search | query | - |
| 回复邀请 | feishu_calendar_event | reply | event_id, rsvp_status | - |
| 查重复日程实例 | feishu_calendar_event | instances | event_id, start_time, end_time | - |
| 查忙闲 | feishu_calendar_freebusy | list | time_min, time_max, user_ids[] | - |
| 邀请参会人 | feishu_calendar_event_attendee | create | calendar_id, event_id, attendees[] | - |
| 删除参会人 | feishu_calendar_event_attendee | batch_delete | calendar_id, event_id, user_open_ids[] | - |

---

## CLI 调用示例

### 创建会议

```bash
feishu-lark call feishu_calendar_event '{
  "action": "create",
  "summary": "项目复盘会议",
  "description": "讨论 Q1 项目进展",
  "start_time": "2026-02-25T14:00:00+08:00",
  "end_time": "2026-02-25T15:30:00+08:00",
  "user_open_id": "ou_aaa",
  "attendees": [
    {"type": "user", "id": "ou_bbb"},
    {"type": "user", "id": "ou_ccc"}
  ]
}'
```

### 查询日程

```bash
feishu-lark call feishu_calendar_event '{
  "action": "list",
  "start_time": "2026-02-25T00:00:00+08:00",
  "end_time": "2026-03-03T23:59:00+08:00"
}'
```

### 查忙闲

```bash
feishu-lark call feishu_calendar_freebusy '{
  "action": "list",
  "time_min": "2026-02-25T09:00:00+08:00",
  "time_max": "2026-02-25T18:00:00+08:00",
  "user_ids": ["ou_aaa", "ou_bbb"]
}'
```

### 搜索日程

```bash
feishu-lark call feishu_calendar_event '{"action": "search", "query": "项目复盘"}'
```

---

## 核心约束

### 1. user_open_id 的作用

工具使用用户身份创建日程（日程在用户主日历上）。传 user_open_id 可以：
- 将发起人添加为参会人
- 确保发起人收到通知和 RSVP
- 确保发起人出现在参会人列表中

获取当前用户 open_id：
```bash
feishu-lark call feishu_get_user '{}'
```

### 2. 参会人类型

- `type: "user"` + `id: "ou_xxx"` — 飞书用户
- `type: "chat"` + `id: "oc_xxx"` — 飞书群组
- `type: "resource"` + `id: "omm_xxx"` — 会议室
- `type: "third_party"` + `id: "email@example.com"` — 外部邮箱

### 3. 会议室预约是异步的

添加会议室后 `rsvp_status: "needs_action"`（预约中），需用 attendee list 查询最终状态。

### 4. instances 仅对重复日程有效

先用 get 检查 `recurrence` 字段是否存在，再调用 instances。

---

## 常见错误

| 错误现象 | 原因 | 解决 |
|---------|------|------|
| 发起人不在参会人列表 | 未传 user_open_id | 传 user_open_id |
| 时间不对 | 使用了 Unix 时间戳 | 使用 ISO 8601 格式 |
| 会议室显示"预约中" | 异步预约 | 等待后查询 rsvp_status |

---

## 附录

### 日历类型

| 类型 | 说明 | 能否删除 |
|------|------|---------|
| primary | 主日历 | 否 |
| shared | 共享日历 | 是 |
| resource | 会议室日历 | 否 |

### 回复状态 (rsvp_status)

| 状态 | 用户含义 | 会议室含义 |
|------|---------|-----------|
| needs_action | 未回复 | 预约中 |
| accept | 已接受 | 预约成功 |
| tentative | 待定 | - |
| decline | 拒绝 | 预约失败 |
