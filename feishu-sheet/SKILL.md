---
name: feishu-sheet
description: |
  飞书电子表格（Sheets）操作。支持创建、读写、查找、导出。
  通过 feishu-lark CLI 调用。

  当以下情况时使用：
  (1) 读写飞书电子表格数据
  (2) 创建电子表格、批量写入数据
  (3) 在表格中查找单元格、导出为 xlsx/csv
  (4) 处理表格中的图片单元格（embed-image）
  (5) 用户提到"电子表格"、"sheet"、"sheets"、"表格"（注意区分多维表格 bitable）
---

# 飞书电子表格 (Sheets)

电子表格（Sheets）类似 Excel/Google Sheets。**不是**多维表格（Bitable/Airtable），二者是不同产品 — 多维表格请用 `feishu_bitable_*` 系列。

## 执行前必读

- **读图片单元格的坑**：默认 `value_render_option=ToString`，图片单元格只返回 `[{"id":N,"type":"embed-image"}]` 占位符，**没有 fileToken**。必须用 `UnformattedValue` 重读才能拿到 fileToken。详见下文 §"图片单元格处理"。
- **write 是覆盖写入，高危**：会清空原范围数据。不确定时先 `read` 确认；追加场景用 `append`。
- **read 上限 200 行**：超出返回 `truncated:true` + `total_rows`，需要缩小 range 重读。
- **write/append 上限**：5000 行 / 100 列。
- **wiki URL**：sheet.ts 内部已自动解析 `wik` 前缀，但若用户给的是不确定类型的 wiki 链接，应先用 `feishu_wiki_space_node` 确认 `obj_type=sheet` 再调用。

---

## 快速索引

| 用户意图 | action | 必填 | 常用可选 |
|---|---|---|---|
| 看表格信息 + 工作表列表 | `info` | url 或 spreadsheet_token | - |
| 读数据 | `read` | url 或 spreadsheet_token | range, sheet_id, value_render_option |
| 读含图片的单元格 | `read` | url + value_render_option:"UnformattedValue" | range |
| 覆盖写入 | `write` | url, values | range, sheet_id |
| 末尾追加行 | `append` | url, values | range, sheet_id |
| 查找单元格 | `find` | url, sheet_id, find | match_case, search_by_regex |
| 创建电子表格 | `create` | title | folder_token, headers, data |
| 导出 xlsx/csv | `export` | url, file_extension | sheet_id（csv 必填）, output_path |

---

## CLI 调用示例

### 获取表格信息

```bash
feishu-lark call feishu_sheet '{"action":"info","url":"https://xxx.feishu.cn/sheets/TOKEN"}'
```

### 读取数据

```bash
feishu-lark call feishu_sheet '{
  "action":"read",
  "url":"https://xxx.feishu.cn/sheets/TOKEN",
  "range":"Qu2odS!A1:E40"
}'
```

### 创建带初始数据的电子表格

```bash
feishu-lark call feishu_sheet '{
  "action":"create",
  "title":"客户列表",
  "headers":["姓名","部门","入职日期"],
  "data":[["张三","工程","2026-01-01"]]
}'
```

### 末尾追加行

```bash
feishu-lark call feishu_sheet '{
  "action":"append",
  "url":"https://xxx.feishu.cn/sheets/TOKEN",
  "sheet_id":"Qu2odS",
  "values":[["李四","设计","2026-02-01"]]
}'
```

---

## ⚠️ 图片单元格（embed-image）处理

电子表格的单元格可以嵌入图片。**默认渲染方式拿不到图片资源，必须按下面的流程处理**。

### 识别

读取后，如果某个单元格的值长这样，就是图片占位符：

```json
[{"id": 45, "type": "embed-image"}]
```

⚠️ **这是占位符，不是空数据，也不是"没有图片"** — 不要据此回复用户"该单元格无图片"。

### 正确流程

#### 步骤 1：用 `UnformattedValue` 重读，拿到 fileToken

```bash
feishu-lark call feishu_sheet '{
  "action":"read",
  "url":"https://xxx.feishu.cn/sheets/TOKEN",
  "range":"Qu2odS!E40:E40",
  "value_render_option":"UnformattedValue"
}'
```

返回示例：

```json
{
  "range": "Qu2odS!E40:E40",
  "values": [[{
    "fileToken": "NYTCbJ2a4oB8rUxxQGfcErQpnEh",
    "height": 2364,
    "width": 1773,
    "link": "https://internal-api-drive-stream.larkoffice.com/...",
    "text": "",
    "type": "embed-image"
  }]]
}
```

#### 步骤 2：用 `feishu_doc_media` 下载

```bash
feishu-lark call feishu_doc_media '{
  "action":"download",
  "resource_type":"media",
  "resource_token":"NYTCbJ2a4oB8rUxxQGfcErQpnEh",
  "output_path":"/tmp/cell_E40.png"
}'
```

> 注：`link` 字段是内部直链（含 `mount_node_token` 等参数），不要尝试直接 GET，请走 `feishu_doc_media` 下载，自动带上认证。

### 何时主动用 `UnformattedValue`

- 用户明确说"读图片"、"取出表格里的图"
- 用户给的 range 已知含图片列
- 第一次 `read` 后看到任何 `{"type":"embed-image"}` 占位符 → 立即对该范围用 `UnformattedValue` 重读

### 取舍

`UnformattedValue` 会让其它单元格也变成"原始值"形态（数字不带格式、日期变成数值）。如果只关心图片所在的几个单元格，**只对那几个单元格的 range 用 `UnformattedValue`**，文本数据仍用默认 `ToString`。

---

## value_render_option 速查

| 取值 | 用途 | 图片单元格表现 |
|---|---|---|
| `ToString`（默认） | 文本数据，按显示渲染 | `[{id, type:"embed-image"}]` 占位符 ❌ |
| `FormattedValue` | 按格式渲染（带千分位、日期格式等） | 同上占位符 ❌ |
| `Formula` | 返回公式原文 | 占位符 ❌ |
| `UnformattedValue` | 原始值 | `{fileToken, link, ...}` ✅ |

**结论**：要读图片，**只能**用 `UnformattedValue`。

---

## Wiki URL 处理

知识库链接 `https://xxx.feishu.cn/wiki/TOKEN` 背后可能是云文档、电子表格、多维表格等不同类型，**不能假设是 sheet**。

### 处理流程

1. 先调用 `feishu_wiki_space_node`（action: get）解析：

   ```bash
   feishu-lark call feishu_wiki_space_node '{"action":"get","token":"wiki_token"}'
   ```

2. 检查返回的 `node.obj_type`：
   - `sheet` → 用 `feishu_sheet`，传 `spreadsheet_token = obj_token`
   - `docx` → 走 `feishu_fetch_doc`
   - `bitable` → 走 `feishu_bitable_*` 系列
   - 其他 → 告知用户暂不支持

> 注：本工具内部对 `wik` 前缀已做自动解析，所以**直接传 wiki URL 也能工作**。但若用户场景含混，建议先确认类型避免误用。

---

## 工具组合

| 需求 | 工具 |
|---|---|
| 读电子表格数据 | `feishu_sheet` (action=read) |
| 下载表格里的图片 | `feishu_sheet` (UnformattedValue) → `feishu_doc_media` (download) |
| 解析 wiki token 类型 | `feishu_wiki_space_node` (action=get) |
| 处理云文档 | `feishu_fetch_doc` |
| 操作多维表格 | `feishu_bitable_*` 系列 |

---

## 常见错误

| 现象 | 原因 | 修复 |
|---|---|---|
| 读图片单元格只看到 `[{id, type:"embed-image"}]` | 用了默认 `ToString` | 重读时加 `value_render_option:"UnformattedValue"` |
| 直接 GET `link` 字段 403 | 那是带 token 的内部直链，需要认证 | 改用 `feishu_doc_media` action=download |
| `find` 报错没结果 | `range` 写成 `sheetId!A1:D10` 了 | `find` 的 range 不带 `sheetId!` 前缀，sheet_id 走单独参数 |
| `write` 后原数据不见了 | `write` 是覆盖语义 | 追加场景改用 `append` |
| 数据超过 200 行被截断 | read 默认上限 | 看 `total_rows`，缩小 range 分批读 |
| 把多维表格 URL 传给 sheet 工具 | 多维表格是 bitable，不是 sheet | 用 `feishu_bitable_*` 系列 |
