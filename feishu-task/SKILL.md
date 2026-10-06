---
name: feishu-task
description: |
  飞书任务管理工具，用于创建、查询、更新任务和清单。
  通过 feishu-lark CLI 调用。

  当以下情况时使用：
  (1) 创建、查询、更新、删除任务
  (2) 创建、管理任务清单
  (3) 用户提到"任务"、"待办"、"to-do"、"清单"、"task"
---

# 飞书任务管理

## 执行前必读

- 时间格式：ISO 8601 / RFC 3339（带时区），例如 `2026-02-28T17:00:00+08:00`
- patch/get 必须：task_guid
- tasklist.tasks 必须：tasklist_guid
- 完成任务：completed_at = "2026-02-26 15:00:00"
- 反完成（恢复未完成）：completed_at = "0"

---

## 快速索引

| 用户意图 | 工具 | action | 必填参数 | 常用可选 |
|---------|------|--------|---------|---------|
| 新建待办 | feishu_task_task | create | summary | members, due, description |
| 查未完成任务 | feishu_task_task | list | - | completed=false, page_size |
| 获取任务详情 | feishu_task_task | get | task_guid | - |
| 完成任务 | feishu_task_task | patch | task_guid, completed_at | - |
| 反完成任务 | feishu_task_task | patch | task_guid, completed_at="0" | - |
| 创建清单 | feishu_task_tasklist | create | name | members |
| 查看清单任务 | feishu_task_tasklist | tasks | tasklist_guid | completed |
| 添加清单成员 | feishu_task_tasklist | add_members | tasklist_guid, members[] | - |

---

## CLI 调用示例

### 创建任务

```bash
feishu-lark call feishu_task_task '{
  "action": "create",
  "summary": "准备周会材料",
  "description": "整理本周工作进展和下周计划",
  "due": {"timestamp": "2026-02-28T17:00:00+08:00", "is_all_day": false},
  "members": [
    {"id": "ou_xxx", "role": "assignee"}
  ]
}'
```

### 查未完成任务

```bash
feishu-lark call feishu_task_task '{"action": "list", "completed": false, "page_size": 20}'
```

### 完成任务

```bash
feishu-lark call feishu_task_task '{"action": "patch", "task_guid": "xxx", "completed_at": "2026-02-26 15:30:00"}'
```

### 反完成（恢复未完成）

```bash
feishu-lark call feishu_task_task '{"action": "patch", "task_guid": "xxx", "completed_at": "0"}'
```

### 创建清单

```bash
feishu-lark call feishu_task_tasklist '{
  "action": "create",
  "name": "产品迭代 v2.0",
  "members": [{"id": "ou_xxx", "role": "editor"}]
}'
```

---

## 核心约束

### 1. 工具使用用户身份

- 只能查看和编辑自己是成员的任务
- 创建时建议将自己加入 members，否则后续无法编辑

获取当前用户 open_id：
```bash
feishu-lark call feishu_get_user '{}'
```

### 2. 成员角色

- **assignee（负责人）**：负责完成任务，可编辑
- **follower（关注人）**：关注进展，接收通知

### 3. completed_at 三种用法

| 用途 | 值 |
|------|---|
| 完成 | `"2026-02-26 15:30:00"` |
| 反完成 | `"0"` |
| 毫秒时间戳 | `"1740545400000"` |

### 4. 清单成员角色

| 角色 | 说明 |
|------|------|
| owner | 所有者（创建者自动成为） |
| editor | 可编辑 |
| viewer | 只读 |

---

## 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| 创建后无法编辑 | 未将自己加入 members | 创建时添加为 assignee/follower |
| patch 失败 | 未传 task_guid | 必须传 task_guid |
| 反完成失败 | completed_at 格式错误 | 使用字符串 `"0"` |
