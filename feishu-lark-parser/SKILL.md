---
name: feishu-lark-parser
description: |
  使用 LarkParser 将飞书文档转换为高质量 Markdown。相比 feishu_fetch_doc 提供更丰富的能力：AI 图片描述生成、AI 表头提取、Agent 友好模式（画板/白板转 mermaid）。通过 feishu-lark CLI 调用：`feishu-lark call feishu_lark_parser '<json>'`
---

# feishu_lark_parser

使用 LarkParser 服务将飞书文档转换为高质量 Markdown。

## CLI 调用方式

```bash
feishu-lark call feishu_lark_parser '<json>'
```

示例：

```bash
# 基础用法 - 快速转换
feishu-lark call feishu_lark_parser '{"url":"https://bytedance.larkoffice.com/docx/PUardkIAQosQDfx0PTecPpsanIc"}'

# 启用 AI 图片描述
feishu-lark call feishu_lark_parser '{"url":"https://bytedance.larkoffice.com/docx/xxxxx","enable_image_caption":true}'

# 严格模式 + Agent 友好
feishu-lark call feishu_lark_parser '{"url":"https://bytedance.larkoffice.com/wiki/xxxxx","mode":"strict","agent_friendly":true}'
```

## 与 feishu_fetch_doc 的区别

| 特性 | feishu_fetch_doc | feishu_lark_parser |
|------|-----------------|-------------------|
| 输入 | doc_id（token 或 URL） | url（完整飞书链接） |
| AI 图片描述 | 不支持 | 支持（enable_image_caption） |
| AI 表头提取 | 不支持 | 支持（enable_table_header_extract） |
| 画板/白板 | 返回 token 标签 | Agent 友好模式返回 mermaid |
| Wiki 处理 | 需先用 wiki_space_node 解析 | 直接传 wiki URL 即可 |
| 重试策略 | 无 | fast/retry/strict 三种模式 |
| 元数据 | 仅标题 | 标题、作者、更新者、时间等 |

## 参数

- **`url`**（必填）：飞书文档完整链接
  - 支持 docx、wiki、sheet、bitable 等类型的链接
  - 例如 `https://bytedance.larkoffice.com/docx/xxxxx`

- **`mode`**（可选，默认 `fast`）：转换模式
  - `fast`: 快速模式，不重试
  - `retry`: 重试模式，重试 3 次，限流时不重试
  - `strict`: 严格模式，重试 3 次，限流时也重试

- **`enable_image_caption`**（可选，默认 `false`）：是否启用 AI 图片描述生成

- **`enable_table_header_extract`**（可选，默认 `false`）：是否启用 AI 表格表头提取

- **`agent_friendly`**（可选，默认 `true`）：Agent 友好模式
  - `true`: 画板/白板返回 mermaid 代码块
  - `false`: 返回 base64 图片

## 环境变量

- **`LARK_PARSER_REGION`**：选择 API 端点区域（`cn` 或 `i18n`，默认 `cn`）
- **`LARK_PARSER_ENDPOINT`**：自定义 API 端点 URL（优先级高于 REGION）

## 使用建议

- **需要 AI 增强能力时**（图片描述、表头提取、mermaid 画板）→ 使用 `feishu_lark_parser`
- **简单获取文档内容时** → 使用 `feishu_fetch_doc`（更轻量）
- **需要分页获取大文档时** → 使用 `feishu_fetch_doc`（支持 offset/limit）

## 工具组合

| 需求 | 工具 |
|------|------|
| 高质量文档转换（含 AI 能力） | `feishu_lark_parser` |
| 基础文档获取 | `feishu_fetch_doc` |
| 创建文档 | `feishu_create_doc` |
| 更新文档 | `feishu_update_doc` |
| 下载图片/文件 | `feishu_doc_media`（action: download） |
