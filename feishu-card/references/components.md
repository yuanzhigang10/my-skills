# Feishu Card Components Quick Reference

Use this as the compact lookup for Feishu card JSON v2. Prefer v2 cards with top-level `"schema": "2.0"` and `body.elements`.

Official docs worth checking when precision matters:
- Card JSON 2.0 structure: https://open.feishu.cn/document/feishu-cards/card-json-v2-structure
- JSON 2.0 components overview: https://open.feishu.cn/document/feishu-cards/card-json-v2-components/components-overview
- Collapsible panel: https://open.feishu.cn/document/feishu-cards/card-json-v2-components/containers/collapsible-panel

## Card Shell

```json
{
  "schema": "2.0",
  "config": {
    "update_multi": true,
    "width_mode": "fill",
    "enable_forward": true,
    "summary": { "content": "消息摘要" }
  },
  "header": {
    "template": "blue",
    "title": { "tag": "plain_text", "content": "标题" }
  },
  "body": {
    "direction": "vertical",
    "vertical_spacing": "medium",
    "padding": "12px 12px 12px 12px",
    "elements": []
  }
}
```

Notes:
- v2 requires Feishu client 7.20+.
- Keep one card under 30 KB and roughly under 200 elements.
- `update_multi` is effectively shared-card mode in v2; do not set it to `false`.

## Text

### `markdown`

Best default for rich content, summaries, lists, code, tables, links, mentions, and inline tags.

```json
{
  "tag": "markdown",
  "element_id": "summary",
  "content": "**结论**：完成率 <font color='green'>96%</font>，异常 <font color='red'>3</font>。\n\n<font color='grey'>更新时间：10:00</font>",
  "text_size": "normal",
  "text_align": "left",
  "margin": "0"
}
```

Useful inline tags:
- `<font color='red|green|blue|grey|orange|rgba(...)'>text</font>`
- `<at id='ou_xxx'></at>` and `<at id='all'></at>`
- `<person id='ou_xxx' show_name=true show_avatar=true></person>`
- `<text_tag color='blue'>进行中</text_tag>`
- `<link url='https://...' pc_url='...' ios_url='...' android_url='...'>打开</link>`
- `<local_datetime millisecond='1713600000000' format_type='date_time'></local_datetime>`
- `<raw>literal markdown</raw>`

Pitfalls:
- Use a blank line for reliable paragraph breaks.
- v2 does not support old `[text]($urlVal)` differentiated links; use `<link>`.
- Hex colors are not generally accepted inside `<font>`; use named colors or rgba.

### `div`

Use for compact key-value blocks. `fields[].is_short: true` makes a two-column layout.

```json
{
  "tag": "div",
  "text": { "tag": "lark_md", "content": "**发布结果**" },
  "fields": [
    { "is_short": true, "text": { "tag": "lark_md", "content": "**版本**\n1.2.3" } },
    { "is_short": true, "text": { "tag": "lark_md", "content": "**状态**\n<font color='green'>成功</font>" } }
  ]
}
```

Pitfall: keep fields to 2 or 4 items when possible. Dense 6+ field blocks become hard to scan on mobile.

## Media And Data

### `img`

```json
{
  "tag": "img",
  "img_key": "img_v2_xxx",
  "alt": { "tag": "plain_text", "content": "截图" },
  "mode": "fit_horizontal",
  "preview": true
}
```

Pitfall: v2 has no `stretch_without_padding`; use negative horizontal margin such as `"margin": "0 -12px"` only when a full-bleed image is intentional.

### `chart`

```json
{
  "tag": "chart",
  "element_id": "chart_1",
  "aspect_ratio": "16:9",
  "height": "auto",
  "color_theme": "brand",
  "preview": true,
  "chart_spec": {
    "type": "bar",
    "data": { "values": [{ "name": "A", "value": 10 }] },
    "xField": "name",
    "yField": "value"
  }
}
```

Pitfalls:
- Keep to 5 charts or fewer per card.
- Blank charts are usually field-name mismatches between `chart_spec` and `data.values`.
- See `vchart.md` for chart spec templates.

### `table`

```json
{
  "tag": "table",
  "page_size": 5,
  "row_height": "low",
  "columns": [
    { "name": "name", "display_name": "名称", "data_type": "lark_md", "width": "auto" },
    { "name": "status", "display_name": "状态", "data_type": "options", "width": "100px" }
  ],
  "rows": [
    { "name": "**任务 A**", "status": [{ "text": "完成", "color": "green" }] }
  ]
}
```

Pitfalls:
- `rows` keys must exactly match `columns[].name`.
- Put `table` directly under `body.elements` or inside `interactive_container`; avoid nesting in `column_set`, `collapsible_panel`, or `form`.
- For nested layouts, use a markdown table instead.

## Layout Containers

### `column_set`

```json
{
  "tag": "column_set",
  "flex_mode": "bisect",
  "horizontal_spacing": "medium",
  "columns": [
    { "tag": "column", "width": "weighted", "weight": 1, "elements": [] },
    { "tag": "column", "width": "weighted", "weight": 1, "elements": [] }
  ]
}
```

Use:
- `bisect` for two equal columns.
- `trisect` for three equal columns.
- `flow` when narrow screens should wrap.
- `width: "weighted"` plus `weight` for custom ratios.

Pitfall: v2 does not accept numeric `column.width`; write `"width": "weighted", "weight": 2`.

### `collapsible_panel`

```json
{
  "tag": "collapsible_panel",
  "expanded": false,
  "header": { "title": { "tag": "plain_text", "content": "详细信息" } },
  "elements": [
    { "tag": "markdown", "content": "次要内容放这里" }
  ]
}
```

Use collapsed panels for long logs, secondary context, and appendix-like details.

### `form`

Use for input collection. Give each input a stable `name` and each interactive element a stable `element_id`.

### `interactive_container`

Use when the whole block should be clickable or when direct table placement is not enough. Keep nested interactions simple to avoid confusing event handling.

## Interactive Controls

Common tags:
- `button`: primary action, link, or callback.
- `input`: one-line text.
- `textarea`: longer text.
- `select_static` / `multi_select`: fixed options.
- `date_picker`: date input.
- `overflow`: compact menu for secondary actions.
- `checker`: checkbox-like selection.

Button skeleton:

```json
{
  "tag": "button",
  "text": { "tag": "plain_text", "content": "查看详情" },
  "type": "primary",
  "width": "default",
  "behaviors": [
    { "type": "open_url", "default_url": "https://example.com" }
  ]
}
```

Feishu sidebar AppLink button:

```json
{
  "tag": "button",
  "text": { "tag": "plain_text", "content": "右侧看 Review" },
  "type": "default",
  "width": "fill",
  "behaviors": [
    {
      "type": "open_url",
      "default_url": "https://example.com/detail?id=123",
      "pc_url": "https://applink.feishu.cn/client/web_url/open?mode=sidebar-semi&url=https%3A%2F%2Fexample.com%2Fdetail%3Fid%3D123&max_width=800&reload=false",
      "ios_url": "https://example.com/detail?id=123",
      "android_url": "https://example.com/detail?id=123"
    }
  ]
}
```

Use sidebar AppLink for heavy detail pages such as git diff, code review, logs, dashboards, or trace viewers. Keep the card as summary + next action; put the full inspection surface in the side panel. Prefer `pc_url` for the sidebar AppLink and keep mobile URLs as the original responsive page. Always URL-encode the inner `url` parameter, and validate both the outer AppLink and the inner target as http(s).

Pitfalls:
- Put primary actions before secondary actions.
- Use `column_set` to align multiple buttons horizontally.
- Avoid placing too many controls in one card; three visible actions is usually enough.

## Header

```json
{
  "template": "blue",
  "title": { "tag": "plain_text", "content": "服务告警" },
  "subtitle": { "tag": "plain_text", "content": "prod / checkout" },
  "icon": { "tag": "standard_icon", "token": "warning_filled", "color": "red" },
  "text_tag_list": [
    { "tag": "text_tag", "text": { "tag": "plain_text", "content": "P1" }, "color": "orange" }
  ]
}
```

Template colors: `blue`, `wathet`, `turquoise`, `green`, `yellow`, `orange`, `red`, `carmine`, `violet`, `purple`, `indigo`, `grey`.

## Generic Layout Properties

Many v2 components accept:
- `element_id`: stable unique id for updates and callbacks.
- `margin`: CSS-like pixels, e.g. `"0 0 8px 0"`.
- `padding`: CSS-like pixels, mostly containers.
- `horizontal_align`: `left`, `center`, `right`.
- `vertical_align`: `top`, `center`, `bottom`.
- `vertical_spacing` / `horizontal_spacing`: `small`, `medium`, `large`, `extra_large`, or pixels.

Use container spacing first. Add per-element margin only for local exceptions.
