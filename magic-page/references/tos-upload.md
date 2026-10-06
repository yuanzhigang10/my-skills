# TOS 文件上传

把本地文件上传到 TOS（ByteDance Object Storage），返回**公开可访问的 URL**。小文件走 `magic.solutionsuite.cn` 匿名代理换预签名 URL，不需要用户 OAuth / 妙笔 token；它不是私有存储。

bot mode 下小文件匿名上传默认允许；multipart 默认禁用，除非显式设置 `botRuntime.tos.allowMultipartUpload=true` / `FEISHU_BOT_TOS_ALLOW_MULTIPART_UPLOAD=true` 并提供合法妙笔 token。TOS URL 是公开链接，包含敏感数据时不要上传。

## 使用工具

`feishu_tos_upload`，action 只有 `upload`：

```bash
feishu-lark call feishu_tos_upload '{
  "action": "upload",
  "file_path": "/tmp/logo.png"
}'
```

返回：

```json
{
  "action": "upload",
  "mode": "single",
  "url": "https://magic-builder.tos-cn-beijing.volces.com/uploads/1700000000000_logo.png",
  "filename": "logo.png",
  "content_type": "image/png",
  "size": 18432
}
```

## 模式判断

| 文件大小 | 模式 | 路径 | 鉴权 |
|---|---|---|---|
| ≤ 16 MB | `single` | `/api/tos/sign` → PUT 预签名 URL | 无需 |
| > 16 MB | `multipart` | `/api/tos/multipart/{init,part,complete}`，10 MB/片 | **需要妙笔 token**；bot mode 默认禁用 |

自动按文件大小选择。**大文件（>16MB）必须先 `feishu-lark magic login` 或设置 `MAGIC_TOKEN`**，否则会报"TOS multipart 上传需要妙笔 token"。bot mode 且 `allowPersonalToken=false` 时不会读取 keychain 里的个人 token。

## 选项

| 字段 | 用途 |
|---|---|
| `key` | 自定义 TOS 存储路径，如 `assets/team-logo.png`。缺省服务端生成 `uploads/<ts>_<filename>` |
| `content_type` | 覆盖 MIME 推断。缺省按文件扩展名自动映射（30+ 常见类型）|
| `record` | `true` 时把小文件**登记进妙笔文件管理**（可在妙笔里 list/delete），需妙笔 token；返回多 `id`/`record_id`。缺省 `false`（匿名上传只回 URL，不进文件列表）。`>16MB` 分片本就登记，此参数仅影响小文件 |

未识别的扩展名 → `application/octet-stream`。

> 注：`record:true` 登记成功返回 `token_source:"recorded"` + `id`；若服务端登记失败会降级为只回 URL，并带 `record_error` 说明原因（URL 仍可用）。只要文件能正常引用，登记失败可忽略。

## 与 `feishu_doc_media` 的边界

| | feishu_tos_upload | feishu_doc_media |
|---|---|---|
| 目的 | 拿公开 URL | 把图片/文件嵌入飞书文档 |
| 鉴权 | 小文件匿名代理；multipart 需要妙笔 token | 飞书 OAuth |
| 输出 | TOS 公开 URL | 文档内的 image/file 块 + 飞书内部 token |
| 资源寿命 | TOS 中长期保存（无 TTL）| 跟随文档，无法独立访问 |
| 适合场景 | 给妙笔 `<img src="...">` 引用；外部分享 | 文档插图 |

**经常同时用**：

```bash
# 1) 上传图到 TOS 拿公开 URL
URL=$(feishu-lark call feishu_tos_upload '{"action":"upload","file_path":"/tmp/cover.png"}' | jq -r .url)

# 2) 在妙笔 HTML 里用这个 URL（推荐 — 体积外置）
cat > /tmp/app.html <<EOF
<img src="$URL" alt="封面" />
...
EOF

# 3) 把妙笔嵌进文档
feishu-lark call feishu_magic_doc '{"action":"create","title":"...","html_path":"/tmp/app.html"}'
```

这样妙笔代码块只存 `<img src=URL/>`，不嵌 base64，**大幅减小文档体积 + 加载更快**。

## 何时不要用 TOS

- 文件包含**敏感数据**（TOS 是公开 URL，任何人能访问）
- 文件需要**访问权限控制**（用飞书云空间 + share 链接代替）
- 文件 < 1KB（直接 base64 嵌进 HTML 更简单）

## 故障排查

| 现象 | 原因 |
|---|---|
| `TOS sign 失败 code=xx` | 服务端拒绝（罕见，可能是文件名含特殊字符）。改 `key` 重试 |
| `TOS PUT 失败 HTTP 403` | 预签名 URL 过期（自取后立即用，不要存超过 5 分钟） |
| URL 200 但内容下载失败 | `Content-Disposition: attachment` —— TOS 默认要求下载而非内联。前端 `<img>` 用法不受影响 |
| 大文件 multipart 中断 | 网络抖动。整体重传（暂未实现断点续传） |

## URL 长寿命

TOS 文件**无 TTL，永久保存**（直到手动 delete）。可以放心用作 README 图、博客封面等长期资产。

## 限制

- 单文件最大 **5 GB**（multipart 上限）
- 单片必须 **5–10 MB**（multipart 服务端限制）
- 上传速率受网络限制（一般 10–50 MB/s）
