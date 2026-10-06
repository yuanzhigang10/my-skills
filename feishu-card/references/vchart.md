# VChart Specs For Feishu Card Charts

Feishu `chart` components embed a VChart `chart_spec`. Use these compact specs as starting points.

## Card Chart Shell

```json
{
  "tag": "chart",
  "element_id": "chart_1",
  "aspect_ratio": "16:9",
  "height": "auto",
  "color_theme": "brand",
  "preview": true,
  "chart_spec": {}
}
```

Notes:
- `aspect_ratio`: `1:1`, `2:1`, `4:3`, `16:9`.
- `height`: `"auto"` or a pixel value in the supported client range.
- `color_theme`: `brand`, `rainbow`, `complementary`, `monochromatic`.
- Keep a card to 5 charts or fewer.
- Mobile can fail on texture fills, conical gradients, and grid word-cloud layout.

## Bar

```json
{
  "type": "bar",
  "data": {
    "values": [
      { "channel": "A", "amount": 12000 },
      { "channel": "B", "amount": 8500 },
      { "channel": "C", "amount": 15200 }
    ]
  },
  "xField": "channel",
  "yField": "amount",
  "label": { "visible": true },
  "legends": { "visible": false }
}
```

Variants:
- Horizontal bar: add `"direction": "horizontal"`.
- Grouped bar: add a series field in data and use `"xField": ["month", "type"]`.
- Stacked bar: grouped bar plus `"stack": true`.

## Line

```json
{
  "type": "line",
  "data": {
    "values": [
      { "date": "05-15", "uv": 320 },
      { "date": "05-16", "uv": 412 },
      { "date": "05-17", "uv": 389 }
    ]
  },
  "xField": "date",
  "yField": "uv",
  "point": { "visible": true },
  "smooth": true,
  "label": { "visible": false }
}
```

Multi-series: add `"seriesField": "name"` and include `name` in each row.

## Area

```json
{
  "type": "area",
  "data": {
    "values": [
      { "month": "Jan", "revenue": 100 },
      { "month": "Feb", "revenue": 150 },
      { "month": "Mar", "revenue": 180 }
    ]
  },
  "xField": "month",
  "yField": "revenue",
  "area": { "style": { "fillOpacity": 0.3 } }
}
```

Use for cumulative trend or volume over time. Use line chart when exact point comparison matters more.

## Pie Or Donut

```json
{
  "type": "pie",
  "data": {
    "values": [
      { "category": "Search", "value": 40 },
      { "category": "Referral", "value": 25 },
      { "category": "Ads", "value": 20 }
    ]
  },
  "categoryField": "category",
  "valueField": "value",
  "label": { "visible": true },
  "legends": { "visible": true, "orient": "bottom" }
}
```

Donut: add `"innerRadius": 0.6`.

## Scatter

```json
{
  "type": "scatter",
  "data": {
    "values": [
      { "cost": 10, "conversion": 0.12, "segment": "A" },
      { "cost": 18, "conversion": 0.18, "segment": "B" }
    ]
  },
  "xField": "cost",
  "yField": "conversion",
  "seriesField": "segment",
  "label": { "visible": false }
}
```

Use scatter for correlation, outliers, and efficiency comparisons.

## Radar

```json
{
  "type": "radar",
  "data": {
    "values": [
      { "metric": "性能", "score": 90, "model": "A" },
      { "metric": "安全", "score": 95, "model": "A" },
      { "metric": "质量", "score": 88, "model": "A" },
      { "metric": "性能", "score": 84, "model": "B" },
      { "metric": "安全", "score": 91, "model": "B" },
      { "metric": "质量", "score": 93, "model": "B" }
    ]
  },
  "categoryField": "metric",
  "valueField": "score",
  "seriesField": "model",
  "legends": { "visible": true }
}
```

Use for 4 to 8 dimensions. Too many dimensions make the shape unreadable.

## Gauge

```json
{
  "type": "gauge",
  "data": { "values": [{ "value": 78 }] },
  "categoryField": "type",
  "valueField": "value",
  "min": 0,
  "max": 100,
  "title": { "text": "完成度" }
}
```

Use for a single percentage or health score.

## Funnel

```json
{
  "type": "funnel",
  "data": {
    "values": [
      { "stage": "访问", "count": 10000 },
      { "stage": "浏览", "count": 5000 },
      { "stage": "加购", "count": 2000 },
      { "stage": "支付", "count": 600 }
    ]
  },
  "categoryField": "stage",
  "valueField": "count",
  "label": { "visible": true }
}
```

Use only when stages are sequential.

## Word Cloud

```json
{
  "type": "wordCloud",
  "data": {
    "values": [
      { "word": "AI", "freq": 100 },
      { "word": "Agent", "freq": 80 },
      { "word": "Card", "freq": 60 }
    ]
  },
  "nameField": "word",
  "valueField": "freq",
  "wordCloudConfig": { "layoutMode": "default" }
}
```

Avoid `layoutMode: "grid"` for mobile cards.

## Combination

```json
{
  "type": "common",
  "data": {
    "id": "main",
    "values": [
      { "month": "Jan", "revenue": 100, "growth": 5 },
      { "month": "Feb", "revenue": 150, "growth": 8 },
      { "month": "Mar", "revenue": 180, "growth": 12 }
    ]
  },
  "series": [
    { "type": "bar", "xField": "month", "yField": "revenue" },
    { "type": "line", "xField": "month", "yField": "growth" }
  ]
}
```

Use when one chart needs both absolute volume and trend/rate.

## Labels And Legends

```json
{
  "label": {
    "visible": true,
    "position": "top",
    "style": { "fontSize": 12 }
  },
  "legends": {
    "visible": true,
    "orient": "bottom",
    "position": "start"
  }
}
```

Troubleshooting:
- Empty chart: field names do not match data keys.
- Crowded axis: shorten labels, reduce rows, or rotate labels in VChart config.
- Mobile failure: remove advanced fills, gradients, and unsupported word-cloud layout.
