# Feishu Card Design Guide

Short rules for cards that are readable in chat, not just valid JSON.

## Color

Choose `header.template` by intent:

| Intent | Template |
| --- | --- |
| neutral notification, weekly report, documentation | `blue` |
| success, completed, shipped | `green` |
| todo, approval, gentle reminder | `orange` |
| warning, degraded, potential risk | `yellow` |
| error, incident, urgent failure | `red` |
| severe incident, P0 | `carmine` |
| analytics, dashboard, insight | `purple` or `indigo` |
| AI assistant, automation | `violet` or `purple` |
| archived, resolved, low priority | `grey` |

Default to `blue` when unsure.

Inline color rules:
- Use one header color, one accent color, and grey for secondary text.
- Highlight only the numbers or words that change interpretation.
- Avoid more than 3 semantic colors in one card.

Good:

```markdown
成功率 <font color='green'>99.2%</font>，失败 <font color='red'>8</font>。
<font color='grey'>数据更新于 10:00</font>
```

## Layout Order

Place information in the order people scan chat cards:

1. Header: what this card is.
2. Summary markdown: the decision or conclusion.
3. Metrics: 2 to 4 key fields with `div.fields` or compact markdown.
4. Evidence: chart, table, image, or short list.
5. Details: collapsible panels for logs, causes, history, or long lists.
6. Actions: primary action first, then secondary actions.
7. Footnote: source, owner, timestamp in grey notation text.

Recommended heavy card skeleton:

```text
header(template)
markdown summary
hr
div.fields metrics
hr
chart or table
collapsible_panel details
column_set buttons
markdown grey footnote
```

## Spacing Rhythm

Use `body.vertical_spacing: "medium"` as the default.

| Spacing | Use |
| --- | --- |
| `small` | dense related lines |
| `medium` | normal body rhythm |
| `large` | between small sections |
| `extra_large` | major section separation |

Prefer `hr` when the topic changes. Prefer spacing when the same topic continues.

## Width And Columns

Use `config.width_mode: "fill"` for dashboards, tables, charts, and long content.

Column patterns:
- Two metrics or chart + explanation: `flex_mode: "bisect"`.
- Three equal status blocks: `flex_mode: "trisect"`.
- Unknown mobile width: `flex_mode: "flow"`.
- Uneven layout: weighted columns such as text `3` and image `2`.

Keep mobile in mind:
- Do not put wide tables inside columns.
- Avoid three-column text blocks with long labels.
- Prefer short metric labels and values that can wrap cleanly.

## Text

Use sizes intentionally:
- Title belongs in `header.title`, not a huge markdown heading.
- `normal` for body, `notation` for source and hints.
- Use `heading-3` or `heading-4` only for internal section titles in long cards.

Keep cards concise:
- Start with the answer, then context.
- Use bullets for lists over 3 items.
- Collapse anything that feels like appendix material.

## Tags And Icons

Header tags:
- 1 to 3 tags maximum.
- Use `red/carmine` for emergency, `orange` for important, `blue` for in-progress, `green` for done, `grey` for archived.

Header icon:
- Use at most one icon.
- Suggested tokens: `bell_filled`, `check-circle_filled`, `warning_filled`, `chart_outlined`.

Emoji:
- Acceptable in section labels when it improves scanning.
- Do not prefix every line with emoji.

## Actions

Action area rules:
- One primary button.
- One or two secondary actions.
- Put destructive or rare actions in `overflow`.
- Use verbs: `查看详情`, `处理告警`, `批准`, `忽略`.

## Common Card Recipes

Notification:
- `blue` header, markdown summary, 2 to 4 fields, optional button.

Alert:
- `red` or `carmine` header, top summary with impact, fields for service/env/time/owner, primary button to dashboard, collapsed diagnostics.

Report:
- `purple` or `indigo` header, key metric fields, chart, table for top items, grey source line.

Approval:
- `orange` header, requester and reason, compact details, primary approve button, secondary reject button.

Success:
- `green` header, result summary, release or task metrics, optional changelog panel.
