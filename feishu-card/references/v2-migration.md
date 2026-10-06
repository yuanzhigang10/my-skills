# Feishu Card v1 To v2 Migration

This skill targets card JSON v2. Use this file when converting older card JSON.

## Detect Version

v2:

```json
{
  "schema": "2.0",
  "body": { "elements": [] }
}
```

v1:
- No `schema`, or `"schema": "1.0"`.
- Top-level `elements`.

## Required Structural Change

```diff
 {
+  "schema": "2.0",
   "config": {},
   "header": {},
-  "elements": []
+  "body": {
+    "elements": []
+  }
 }
```

## Disabled Or Removed Fields

Remove these from v2 cards:

| v1 field/component | v2 replacement |
| --- | --- |
| top-level `elements` | `body.elements` |
| `note` component | `markdown` with `text_size: "notation"` and grey text |
| `action` component | direct buttons in `body.elements`, usually inside `column_set` |
| `fallback` | no custom global fallback |
| `i18n_elements` | component-level i18n fields such as `i18n_content` |
| `config.wide_screen_mode` | `config.width_mode: "fill"` |
| `config.compact_width` | `config.width_mode: "compact"` |
| `config.update_multi: false` | delete it or set `true` |
| `img.size: "stretch_without_padding"` | use normal image sizing; optionally `margin: "0 -12px"` |
| markdown `[text]($urlVal)` | `<link url='' pc_url='' ios_url='' android_url=''>text</link>` |

v2 validates strictly. Unknown or old fields that v1 ignored can reject the entire card.

## Component Changes

### Header Icon

```diff
 "header": {
   "title": { "tag": "plain_text", "content": "标题" },
-  "icon": { "img_key": "img_v2_xxx" },
-  "ud_icon": { "token": "chat_outlined", "style": { "color": "blue" } }
+  "icon": {
+    "tag": "standard_icon",
+    "token": "chat_outlined",
+    "color": "blue"
+  }
 }
```

### Columns

```diff
 {
   "tag": "column_set",
   "columns": [
-    { "tag": "column", "width": 2, "elements": [] }
+    { "tag": "column", "width": "weighted", "weight": 2, "elements": [] }
   ]
 }
```

### Spacing

v2 spacing names:
- `small`: 4px
- `medium`: 8px
- `large`: 12px
- `extra_large`: 16px

If v1 used `large` expecting 16px, migrate to `extra_large`.

## New v2 Capabilities

Useful v2-only features:
- `element_id` for stable updates and interaction handling.
- `config.width_mode` with `fill` and `compact`.
- `config.streaming_mode` and `streaming_config` for streaming updates.
- `config.summary` for chat list preview.
- Common layout properties such as `margin`, `padding`, `horizontal_align`, and `vertical_spacing`.
- Richer markdown: CommonMark tables, nested lists, `<person>`, `<link>`, `<text_tag>`, `<local_datetime>`.
- Component-level i18n content.
- Custom style tokens under `config.style`.

## Migration Checklist

- [ ] Add `"schema": "2.0"`.
- [ ] Move top-level `elements` into `body.elements`.
- [ ] Remove `note`; replace with notation markdown.
- [ ] Remove `action`; place buttons directly or in columns.
- [ ] Replace `wide_screen_mode` and `compact_width` with `width_mode`.
- [ ] Remove `fallback` and `i18n_elements`.
- [ ] Ensure `update_multi` is omitted or `true`.
- [ ] Convert numeric column widths to `width: "weighted"` plus `weight`.
- [ ] Rewrite `header.icon` to the v2 structure.
- [ ] Replace differentiated markdown URL variables with `<link>`.
- [ ] Review spacing: old 16px `large` should become `extra_large`.
- [ ] Run JSON validation before sending.
- [ ] Test in a Feishu client version 7.20 or later.
