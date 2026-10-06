---
name: feishu-bitable
description: |
  飞书多维表格（Bitable）管理。包含 27 种字段类型支持、高级筛选、批量操作和视图管理。
  通过 feishu-lark CLI 调用。

  当以下情况时使用：
  (1) 创建或管理飞书多维表格
  (2) 增删改查多维表格记录
  (3) 管理字段、视图、数据表
  (4) 用户提到"多维表格"、"bitable"、"数据表"
---

# 飞书多维表格 (Bitable)

## 执行前必读

- 默认表的空行坑：`app.create` 自带的默认表中会有空记录！插入数据前先删除空行
- 写记录前：先 `field.list` 获取字段 type/ui_type
- 人员字段：`[{id:"ou_xxx"}]`（数组对象）
- 日期字段：毫秒时间戳（`1674206443000`）
- 单选：字符串（`"选项1"`）
- 多选：字符串数组（`["选项1", "选项2"]`）
- 批量上限：单次 ≤ 500 条

---

## 快速索引

| 用户意图 | 工具 | action | 必填参数 | 常用可选 |
|---------|------|--------|---------|---------|
| 查字段 | feishu_bitable_app_table_field | list | app_token, table_id | - |
| 查记录 | feishu_bitable_app_table_record | list | app_token, table_id | filter, sort |
| 新增一行 | feishu_bitable_app_table_record | create | app_token, table_id, fields | - |
| 批量导入 | feishu_bitable_app_table_record | batch_create | app_token, table_id, records | - |
| 更新一行 | feishu_bitable_app_table_record | update | app_token, table_id, record_id, fields | - |
| 创建表格 | feishu_bitable_app | create | name | folder_token |
| 创建数据表 | feishu_bitable_app_table | create | app_token, name | fields |

---

## CLI 调用示例

### 查字段类型（必做第一步）

```bash
feishu-lark call feishu_bitable_app_table_field '{"action": "list", "app_token": "S404b...", "table_id": "tbl..."}'
```

### 批量导入

```bash
feishu-lark call feishu_bitable_app_table_record '{
  "action": "batch_create",
  "app_token": "S404b...",
  "table_id": "tbl...",
  "records": [
    {"fields": {"客户名称": "Bytedance", "负责人": [{"id": "ou_xxx"}], "签约日期": 1674206443000, "状态": "进行中"}}
  ]
}'
```

### 筛选查询

```bash
feishu-lark call feishu_bitable_app_table_record '{
  "action": "list",
  "app_token": "S404b...",
  "table_id": "tbl...",
  "filter": {
    "conjunction": "and",
    "conditions": [
      {"field_name": "状态", "operator": "is", "value": ["进行中"]}
    ]
  }
}'
```

---

## 字段值格式（最易错）

| type | 字段类型 | 正确格式 | 常见错误 |
|------|---------|---------|---------|
| 11 | 人员 | `[{id: "ou_xxx"}]` | 传字符串 |
| 5 | 日期 | `1674206443000`（毫秒） | 传秒或字符串 |
| 3 | 单选 | `"选项名"` | 传数组 |
| 4 | 多选 | `["选项1", "选项2"]` | 传字符串 |
| 15 | 超链接 | `{link: "...", text: "..."}` | 传字符串 URL |
| 17 | 附件 | `[{file_token: "..."}]` | 传 URL |

详细参考：[字段 Property 配置](references/field-properties.md)、[记录值格式](references/record-values.md)、[完整示例](references/examples.md)

---

## 常见错误码

| 错误码 | 说明 | 解决 |
|--------|------|------|
| 1254064 | 日期格式错误 | 用毫秒时间戳 |
| 1254068 | 超链接格式错误 | 用 `{text, link}` 对象 |
| 1254066 | 人员格式错误 | 用 `[{id: "ou_xxx"}]` |
| 1254015 | 字段值类型不匹配 | 先 list 字段再按类型写 |
| 1254104 | 批量超 500 条 | 分批调用 |

---

## 资源层级

```
App (多维表格应用)
 ├── Table (数据表) ×100
 │    ├── Record (记录/行) ×20,000
 │    ├── Field (字段/列) ×300
 │    └── View (视图) ×200
 └── Dashboard (仪表盘)
```
