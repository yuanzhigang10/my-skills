# 长文档写作手法参考

提炼自一篇高质量的实战调研报告（美国物流实地调研，12 万字符、37 个表格、283 个双语引用块）。适用于调研报告、技术方案、复盘、评审等长文档。核心思想：**让读者用自己选择的深度读完文档**——只读 TL;DR 一屏也完整，逐节下钻也顺畅。

## 1. TL;DR 先行，一屏读完全文

文档第一节就是 `# TL;DR`，用一个大表格承载全部结论：

- 首行跨列放 **Overview callout**：全文 3~5 条核心判断，每条一句话；
- 之后每行一个领域，固定三列 `Domain | Key Findings | To Dos`（发现和待办分列，读者关心"所以呢"时直接看第三列）；
- 每格结尾放 `[View details](锚点链接)` 跳转正文对应章节，支撑"只读 TL;DR、按需下钻"。

骨架：

```markdown
# TL;DR

<lark-table rows="3" cols="3" column-widths="100,800,800">
  <lark-tr>
    <lark-td colspan="3">
      **Overview**
      <callout emoji="dart" background-color="light-orange" border-color="light-orange">
      **结论一标签：**一句话判断。
      **结论二标签：**一句话判断。
      </callout>
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td><text color="gray">Domain</text></lark-td>
    <lark-td><text color="gray">Key Findings</text></lark-td>
    <lark-td><text color="gray">To Dos</text></lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>**领域 A**</lark-td>
    <lark-td>
      <callout emoji="dart" background-color="light-blue" border-color="light-blue">
      1. **【子场景】**发现一…
      1. **【子场景】**发现二…
      [View details](#正文锚点)
      </callout>
    </lark-td>
    <lark-td>
      <callout emoji="hourglass_flowing_sand" background-color="light-blue" border-color="light-blue">
      - **【子场景】**待办一…
      [View details](#正文锚点)
      </callout>
    </lark-td>
  </lark-tr>
</lark-table>
```

## 2. 每章标注阅读时长

H1 标题自带耗时提示，让读者自己分配注意力：

```markdown
# 调研背景｜Background（3min）
# FBT 核心洞察｜FBT Key Findings（20min）
```

## 3. 双语排版：主语言正文 + quote-container 放译文

中文为主文本，英文译文放 `<quote-container>` 紧随其后。引用块在视觉上退后一层，双语不打架；规则全文 100% 一致执行，读者形成稳定预期。（单语文档跳过此条；同样的手法也可用于"结论 + 原始引语"的层级。）

```markdown
仓库侧举证与提报链路繁琐，商家侧对规则理解不足。
<quote-container>
Warehouse reporting workflows are cumbersome, while merchants lack understanding of the rules.
</quote-container>
```

## 4. 章首摘要 callout

每个核心章节开头先放一个 callout，用编号列表给出本章全部结论，细节在后文展开。读者读完章首即可跳过整章。

## 5. 洞察单元四段式：结论 → 问题 → 证据 → 解法

每个洞察小节结构完全固定，读者在任何一节都知道往哪看：

1. **一句话结论段**：这一节的问题本质是什么；
2. **「问题描述｜Problem Statement」二列表格**：左窄列 = 症状短语（如"举证覆盖不全"），右宽列 = 具体事实，**事实必须带数字**（"最多上传 5 张照片""~90%+ 商家已 opt-in""解决耗时 ~1w-1m"）；
3. **现场证据**：`<grid cols="N">` 多列放截图/照片，紧跟问题表格；
4. **「预期解法｜Proposed Approach」二列表格**：左列 = 解法名，右列 = 具体做法。

列宽建议 `200,650` 左右——标签列窄、内容列宽，扫左列即可索引全表。

## 6. 可扫读的标题与标签系统

- 并列洞察用数字 emoji 排序：`## 1️⃣ NCI处理效率`、`## 2️⃣ 效期管理能力`；
- 固定栏目用语义 emoji：`## 🛖 实操场景画像`、`## 📷 用户画像`、`# ⌛️ 下一步`；
- 列表项用**【标签】前缀**做行内分类：`**【入库-NCI】**仓内提报流程优化…`——粗体只落在标签上，正文不加粗。

## 7. 颜色即章节身份

- callout 背景色按主题固定分配：Overview 用 light-orange，主题 A 全部用 light-blue，主题 B 全部用 light-green——同一主题的 findings 和 todos 同色，颜色成为导航线索；
- emoji 语义固定：🎯 `dart` = 发现/结论，⏳ `hourglass_flowing_sand` = 待办，📌 `pushpin` = 提示；
- **克制**：12 万字符全文只有 13 个 callout、3 种底色。callout 一旦泛滥就失去高亮意义。

## 8. 表格当版面用，不只当数据用

- 概念对比：2 列各放一个定义卡（如 FBT vs CBT），底部 `colspan` 跨列贴一张全景图；
- 三列并排 persona 卡片（每格一张设计好的图片）；
- 覆盖度矩阵：`colspan` 标题行 + 单元格 `{align="center"}`；
- 图片组用 `<grid cols="N"><column width="..">` 控制比例，不要竖着一张张堆。

## 9. 分层阅读的链接设计

一篇文档只承载一层信息密度，层与层之间用链接缝合：

- TL;DR → 正文：`[View details](#锚点)`；
- 汇总版 → 详版：`详细洞察请查看：<mention-doc token="..." type="docx">完整报告</mention-doc>`；
- 相关系统/工单：行内链接，不展开。

## 10. 事实带数字，观点配证据

每个论断都有量化支撑（规模、频次、耗时、比例）；每组问题描述后面直接跟现场截图/照片 grid。写不出数字的论断，要么去补证据，要么降级为"待验证假设"写进下一步。

---

## 起手骨架（调研报告/方案通用）

```markdown
# TL;DR
（Overview callout + Domain/Findings/To Dos 表，见第 1 节骨架）

# 背景｜Background（3min）
一段话讲清楚规模与动机，关键数字加粗。

# 方法/方案概览（1min）
覆盖度矩阵表格。

# 核心洞察 A（20min）
<callout>本章结论 1. … 2. …</callout>

## 1️⃣ 洞察一
一句话结论。
「问题描述」表 → 证据 grid → 「预期解法」表

## 2️⃣ 洞察二
…

# ⌛️ 下一步｜Next Step
带 owner 和时间的待办列表。

# Appendix
```
