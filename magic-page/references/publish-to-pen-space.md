# 发布到妙笔空间（Magic Pen Space）

把 HTML 单页应用发布到 [Magic Pen Space](https://magic.solutionsuite.cn)，拿到独立可访问的 URL，可用于外部分享 / 嵌入飞书消息侧边栏 / 多维表 Dashboard 插件 / 飞书 Tab。

## 使用工具

`feishu_magic_page`，action：`publish`（新建/更新）、`extract`（反扒）、`list`（列出）、`delete`（删除）。
publish 时**不传 `app_id` = 新建；传 `app_id` = 更新已有妙笔**（id 复用，URL 不变）。

> **发布上限 900,000 字符**（10 个 HTML 代码块 × 90,000）。超限会前置报错——通常是内联了大资源，先 `feishu_tos_upload` 上传再引用 URL。

## 鉴权前置

第一次用必须配妙笔 token，两种方式任选：

```bash
# 方式 A（推荐）：飞书 OAuth 一键授权，免粘贴
feishu-lark magic login --oauth
# 打印授权链接并自动打开浏览器 → 飞书授权 → 自动轮询拿 token 存 keychain
# 选项：--timeout <秒>(默认600) / --interval <秒>(默认2) / --no-open(只打印链接不自动开浏览器)

# 方式 B：手动粘贴
feishu-lark magic login
# 打印 wiki 引导 → 用户去妙笔机器人 (https://applink.larkoffice.com/T94fcr4NqQPz)
# 输入 dev → 复制 Token → 粘贴
```

两种方式都把 token 加密保存到**同一个 keychain 槽**，后续工具自动取。也可设 `MAGIC_TOKEN` 环境变量覆盖。已有 token 时加 `--force` 覆盖。

## 新建妙笔

```bash
feishu-lark call feishu_magic_page '{
  "action": "publish",
  "html_path": "/tmp/my-app.html",
  "title": "团队投票工具"
}'
```

返回示例：

```json
{
  "action": "publish",
  "mode": "create",
  "app_id": "vjow1Rs5YqM",
  "title": "团队投票工具",
  "is_open_source": false,
  "urls": {
    "html_box": "https://magic.solutionsuite.cn/html-box/vjow1Rs5YqM",
    "dashboard": "https://magic.solutionsuite.cn/dashboard/vjow1Rs5YqM",
    "panel": "https://applink.feishu.cn/client/web_app/open?mode=panel&...",
    "tab": "https://applink.feishu.cn/client/web_app/open?mode=appCenter&..."
  },
  "updated_at": null
}
```

把 `app_id` **记录下来**（建议存到当前对话上下文 / 用户配置文件），下次更新时复用。

## 更新已有妙笔

```bash
feishu-lark call feishu_magic_page '{
  "action": "publish",
  "app_id": "vjow1Rs5YqM",
  "html_path": "/tmp/my-app-v2.html",
  "title": "团队投票工具 (v2)"
}'
```

`mode` 会变成 `update`。URL 不变，**内容立即生效**（CDN 边缘缓存 ≤ 10s）。

## 列出妙笔（list）

```bash
# 我的妙笔（需 token）
feishu-lark call feishu_magic_page '{"action":"list","scope":"mine"}'
# 公开妙笔 + 标题过滤（scope=public 无需 token）
feishu-lark call feishu_magic_page '{"action":"list","scope":"public","title":"投票"}'
```

返回 `records[]`，每条含 `app_id` / `title` / `is_open_source` / `modified` / `url`。用 `app_id` 去 update / delete / extract。

## 删除妙笔（delete）

```bash
feishu-lark call feishu_magic_page '{"action":"delete","app_id":"vjow1Rs5YqM"}'
```

需 token。删前建议先 `list` 确认 `app_id`，**删除不可恢复**。

## 四种 URL 的用途

| 字段 | 用途 |
|---|---|
| `html_box` | 独立 H5 页面，可直接发给外部 / 微信 / 钉钉 |
| `dashboard` | 多维表格 Dashboard 模式插件 |
| `panel` | 飞书消息侧边栏（点开聊天会话 → 右侧打开） |
| `tab` | 飞书应用 Tab 页（机器人详情页可见） |

不需要时直接忽略对应字段，**对前端代码无影响**。

## 与 `feishu_magic_doc` 的边界

|  | feishu_magic_doc | feishu_magic_page |
|---|---|---|
| 用途 | 嵌入到飞书 docx 文档内 | 发布为独立 URL |
| 鉴权 | 默认用户 OAuth；`as=bot` 时走机器人/应用身份且需 `botRuntime.magic.enabled=true` | 妙笔 token；bot mode 默认禁用 keychain 个人 token，优先用 `MAGIC_TOKEN` |
| 输出 | doc_url + 文档内的画板块 | html_box_url + 3 个集成 URL |
| 适合场景 | 文档内插入互动卡片 | 外部分享、侧边栏、Dashboard |

**经常同时用**：先 `feishu_magic_page publish` 拿到 `html_box_url`，再 `feishu_magic_doc create` 把同样的 HTML 也嵌入到文档里（两者并存，独立维护）。

## 故障排查

| 现象 | 原因 | 解决 |
|---|---|---|
| `未找到妙笔 token` | 没跑 `magic login` | `feishu-lark magic login` 粘贴 token |
| 401 错误 | token 过期/被撤销 | `feishu-lark magic login --force` 拿新 token |
| 更新后内容没变 | 边缘 CDN 缓存 | 加 `?_=$(date +%s)` 强刷或等 10 秒 |
| `is_open_source` 影响什么 | 妙笔空间内的展示标签 | 团队内分享时建议 `true`，外部分享视情况 |

## 进阶：开源标记

```bash
feishu-lark call feishu_magic_page '{
  "action": "publish",
  "html_path": "/tmp/app.html",
  "title": "示例妙笔",
  "is_open_source": true
}'
```

标记为开源后，**其他用户能在妙笔空间看到你的应用并复用**。适合内部分享通用模板。
