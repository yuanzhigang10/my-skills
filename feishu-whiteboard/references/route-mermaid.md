# Route: Mermaid

Mermaid 是**最省 token** 的方案——你只写几行声明式语法，`whiteboard-cli` 帮你自动布局 + 转成飞书画板节点。

## 何时用

| 选 Mermaid | 选 SVG/DSL |
|---|---|
| 流程图 / 时序图 / 类图 / 状态图 / ER / 甘特 / 思维导图 / 饼图 | 自由设计、海报、信息图、几何复杂 |
| 节点 < 50 | 大量自定义美学 |
| 内容大于美观 | 美观大于布局自动化 |
| 接口/系统类技术文档 | 业务汇报、品牌物料 |

## 调用

```bash
# 内联（短图）
feishu-lark call feishu_whiteboard '{
  "action": "draw",
  "doc_id": "<doc_url>",
  "from": "mermaid",
  "content": "flowchart TD\n  A --> B"
}'

# 落盘（长图，推荐）
cat > /tmp/wb-demo/seq.mmd <<'EOF'
sequenceDiagram
  participant U as User
  participant API
  U->>API: GET /thing
  API-->>U: 200
EOF

feishu-lark call feishu_whiteboard '{
  "action": "draw",
  "doc_id": "<doc_url>",
  "input_path": "/tmp/wb-demo/seq.mmd"
}'
```

## 各图谱语法

### flowchart / graph（流程图）

```mermaid
flowchart TD
  A[圆角矩形] --> B{菱形判断}
  B -- 是 --> C[(数据库)]
  B -- 否 --> D((圆形))
  C --> E[/平行四边形/]
  F[\反向斜角\] --> G[/正向斜角/]
```

- 方向：`TD`(上下) / `LR`(左右) / `RL` / `BT`
- 形状：`[]`矩形 / `()`圆角 / `(())`圆 / `{}`菱形 / `[/...\]`梯形 / `[()]`圆柱 / `>...]`旗形
- 样式：
  ```mermaid
  classDef hot fill:#FEE3E2,stroke:#D25D5A,color:#1F2329
  class A,B hot
  ```

### sequenceDiagram（时序图）

```mermaid
sequenceDiagram
  participant U as 用户
  participant API
  participant DB
  U->>API: POST /order
  activate API
  API->>DB: INSERT
  DB-->>API: id
  API-->>U: 201 Created
  deactivate API
  Note over U,API: 跨列注释
  alt 库存不足
    API-->>U: 409 Conflict
  end
```

- 箭头：`->` 实线无头 / `->>` 实线箭头 / `-->>` 虚线箭头（响应）/ `-x` 失败
- `activate`/`deactivate` 显示生命周期条
- `Note over A,B`：跨列注释
- `alt`/`else`/`opt`/`loop`/`par`：流程分支

### classDiagram

```mermaid
classDiagram
  class Animal {
    +String name
    +int age
    +eat()
  }
  class Dog {
    +bark()
  }
  Animal <|-- Dog
  Animal *-- Tail : 组合
  Animal o-- Owner : 聚合
```

- 关系：`<|--`继承 / `*--`组合 / `o--`聚合 / `..>`依赖 / `<--`关联

### erDiagram

```mermaid
erDiagram
  USER ||--o{ ORDER : places
  ORDER ||--|{ ORDER_ITEM : contains
  ORDER_ITEM }|--|| PRODUCT : refers

  USER { string id PK
    string name
    string email
  }
```

- 基数：`||`一 / `o|`零或一 / `|{`一或多 / `o{`零或多

### stateDiagram-v2

```mermaid
stateDiagram-v2
  [*] --> 待审核
  待审核 --> 已通过 : approve
  待审核 --> 已驳回 : reject
  已通过 --> [*]
  已驳回 --> 待审核 : 重新提交
```

### gantt

```mermaid
gantt
  title 项目排期
  dateFormat YYYY-MM-DD
  section 设计
    需求       :done,    des1, 2026-05-01, 5d
    评审       :active,  des2, after des1, 2d
  section 开发
    实现       :         impl, after des2, 10d
```

### pie

```mermaid
pie title 渠道分布
  "直通车" : 35
  "推荐" : 25
  "搜索" : 20
  "其他" : 20
```

### mindmap

```mermaid
mindmap
  root((飞书画板))
    输入
      SVG
      Mermaid
      DSL
    能力
      端到端
      可编辑
```

### journey

```mermaid
journey
  title 下单旅程
  section 浏览
    打开 App: 5: 用户
    搜索商品: 4: 用户
  section 购买
    加入购物车: 5: 用户
    结算: 3: 用户, 系统
```

### timeline

```mermaid
timeline
  title Claude 模型迭代
  2024 : Claude 3
  2025 : Claude 3.5 : Claude 3.7
  2026 : Claude 4 : Claude 4.5 : Claude 4.6 : Claude 4.7
```

## 美化技巧

Mermaid 默认配色平凡。提升观感：

1. **加 `classDef` 用经典色板**（[`style.md`](style.md)）
   ```mermaid
   classDef pri fill:#F0F4FC,stroke:#5178C6,color:#1F2329
   class A,B pri
   ```
2. **关键节点用对比色**：起止节点用强调色（`#1F2329` 黑）
3. **分组用 `subgraph`** + 单独 classDef
4. **`linkStyle 0,1 stroke:#BBBFC4,stroke-width:2`** 弱化连线

## 限制

- **节点过密**：> 50 个节点时 dagre 布局会拥挤，考虑拆图或改 SVG 自由布局
- **不支持 flowchart-elk**：whiteboard-cli 默认 dagre，不要混用 elk 实验布局
- **gitGraph**：解析正常但样式简单
- **xychart-beta / requirementDiagram**：稳定性差，建议绕开
- **超长 label 文字溢出**：手动换行 `<br/>` 或缩短

## 检查清单

- [ ] 选对图谱类型（flowchart vs sequenceDiagram 等）
- [ ] 节点 ≤ 50（否则拆图）
- [ ] 中文 label 用 `"..."` 包裹（含空格/中文标点必加）
- [ ] 关键节点上了 classDef 强调色
- [ ] 用 `--check` 检查无 text-overflow
