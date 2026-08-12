# SMB Lending Lens: 数据探索

> 理解业务数据是构建 AI Agent 的第一步。这节课带你深入探索贷款业务的数据世界。

---

## 概览

上节课我们了解了 AI Agent 项目的框架：Database + Tools + Prompt + Context + Workflow。

这节课，我们来"填空"——深入理解这个项目的数据。

**为什么这很重要？**

想象你刚加入一家新公司，老板说"帮我分析一下贷款数据"。你打开数据库，看到 10 张表、几万条记录。怎么开始？

答案是：**有方法地探索**。

这节课就是教你这个方法。你会：
- 阅读 4 份文档，了解数据的全貌
- 用 DBeaver 连接数据库，亲手跑 SQL
- 遇到不懂的，直接问 AI

**AI 是你的探索伙伴。** 不会写 SQL？问 AI。看不懂字段含义？问 AI。想验证某个假设？让 AI 帮你写查询。

---

## 学习目标

完成这节课后，你将：

1. 掌握探索陌生数据库的方法论
2. 理解贷款业务的完整数据流程
3. 学会阅读 ER 图，理解表与表的关系
4. 熟悉 15+ 个关键业务指标的计算方式
5. 能够用 SQL 回答基本的业务问题

---

## 前置知识

- SQL 基础（SELECT, JOIN, GROUP BY, WHERE）
- 完成 01-Project-Overview
- 已安装 DBeaver（或其他数据库客户端）

---

## 阅读指南

这节课的核心是**阅读 + 探索**。你需要按顺序阅读 4 份文档，边读边动手验证。

**重要提示：** 遇到任何不懂的地方，**立刻问 AI**。可以用 `/teach-start` 进入互动模式，AI 会帮你理解概念、写 SQL、解释结果。

---

### 第一步：了解项目背景

**文档：** [`project.README.md`](project.README.md)

**目标：** 理解这个项目要解决什么业务问题

**阅读要点：**

1. Pacific Bridge Lending 是什么公司？
2. AI Agent 能做哪 5 类分析？
3. 数据库有多少张表？覆盖什么业务流程？

**你会看到：**

```
企业客户 → 提交贷款申请 → 信贷审批 → 发放贷款 → 按月还款 → 正常结清 / 违约
```

这就是整个业务的数据流。后面你看到的每张表，都对应这个流程中的某个环节。

> **关键洞察：** 数据是业务的镜像。理解了业务流程，表结构就不再神秘。

---

### 第二步：深入理解表结构

**文档：** [`docs/dataset/database-table-walkthrough-CN.md`](docs/dataset/database-table-walkthrough-CN.md)

**目标：** 了解每张表存什么数据，字段是什么意思

**这是最重要的一步！**

这份文档按「依赖关系」从简单到复杂讲解 10 张表：

| 层级 | 表 | 说明 |
|------|-----|------|
| 第一层 | industry, risk_grade, loan_status, loan_officer | 配置表，不依赖其他表 |
| 第二层 | customer | 客户表，依赖 industry |
| 第三层 | application, loan | 业务流程表 |
| 第四层 | repayment_schedule, payment, default_event | 交易明细表 |

**动手探索：**

1. 打开 DBeaver，连接到项目数据库（`tmp/data.sqlite`）
2. 对每张表，运行：

```sql
-- 看看表里有什么
SELECT * FROM industry LIMIT 5;

-- 数一数有多少条记录
SELECT COUNT(*) FROM industry;
```

3. 不会写 SQL？直接问 AI：

> "帮我写一个 SQL，查看 customer 表的前 10 条记录，包括他们所属的行业名称"

AI 会给你：

```sql
SELECT c.*, i.industry_name
FROM customer c
JOIN industry i ON c.industry_id = i.id
LIMIT 10;
```

**特别关注：**

- `risk_grade` 表的 `implied_default_rate`（定价假设违约率）
- `customer` 表的 `is_repeat_customer`（是否回头客）
- `payment` 表的 `days_late`（逾期天数）
- `default_event` 表的 `had_early_warning`（是否有早期预警）

这些字段是后面业务分析的关键。

> **关键洞察：** 不要试图一次记住所有字段。先建立整体印象，需要时再查文档。

---

### 第三步：理解表之间的关系

**文档：** [`tmp/fintech_smb_lending_pipeline_medium_er_document.md`](tmp/fintech_smb_lending_pipeline_medium_er_document.md)

**目标：** 学会阅读 ER 图，理解外键关系

**什么是 ER 图？**

ER 图（Entity-Relationship Diagram）用图形展示表与表之间的关系。

```
customer ||--o{ application : "submits"
```

这行的意思是：一个 customer 可以提交多个 application（一对多关系）。

**关键概念：数据库范式 & 反范式化**

你可能注意到，`loan` 表里既有 `application_id`，又有 `customer_id`。按理说，`customer_id` 可以通过 `application` 表间接获取，为什么还要存一份？

这就是**反范式化（Denormalization）**。

- **范式化**：不存重复数据，通过 JOIN 查询
- **反范式化**：冗余存储，换取查询性能

`loan.customer_id` 是冗余的，但它让很多查询少一次 JOIN，性能更好。

**不懂就问 AI：**

> "ER 图里的 `||--o{` 符号是什么意思？"

> "为什么 loan 表里要同时存 application_id 和 customer_id？"

**动手验证：**

```sql
-- 验证 application -> loan 是 1:1 关系
SELECT application_id, COUNT(*)
FROM loan
GROUP BY application_id
HAVING COUNT(*) > 1;
-- 如果返回空，说明确实是 1:1

-- 验证 customer -> loan 是 1:N 关系
SELECT customer_id, COUNT(*) AS loan_count
FROM loan
GROUP BY customer_id
ORDER BY loan_count DESC
LIMIT 5;
-- 看看最多的客户有几笔贷款
```

> **关键洞察：** ER 图是数据库的"地图"。遇到复杂查询，先看 ER 图想清楚 JOIN 路径。

---

### 第四步：学习业务指标和 SQL

**文档：** [`docs/dataset/fintech_smb_lending_pipeline_medium_sql_queries.md`](docs/dataset/fintech_smb_lending_pipeline_medium_sql_queries.md)

**目标：** 学习 20 个实战 SQL 查询，理解业务分析的思路

**这是最硬核的一步！**

这份文档包含 20 个真实的业务查询，每个都有：
- 业务背景（为什么要做这个分析）
- SQL 代码
- 预期结果说明

**推荐阅读顺序：**

1. **Query 1: 风险定价分析** — 核心分析场景 Q1
2. **Query 2: 组合集中度** — 核心分析场景 Q2
3. **Query 5: 客户生命周期价值** — 核心分析场景 Q5
4. **Query 8: 还款行为队列分析** — 理解 CTE（公用表表达式）
5. 其他感兴趣的查询

**动手运行：**

打开 DBeaver，复制文档中的 SQL，实际运行看看结果。

比如 Query 1（风险定价分析）：

```sql
SELECT
    rg.grade_code,
    rg.implied_default_rate AS pricing_assumption_pct,
    ROUND(100.0 * COUNT(de.id) / COUNT(l.id), 2) AS actual_default_rate_pct,
    ROUND(rg.implied_default_rate - (100.0 * COUNT(de.id) / COUNT(l.id)), 2) AS pricing_gap_pct
FROM risk_grade rg
JOIN loan l ON rg.id = l.risk_grade_id
LEFT JOIN default_event de ON l.id = de.loan_id
GROUP BY rg.id
ORDER BY pricing_gap_pct ASC;
```

运行后，你会看到 C 级贷款的 `pricing_gap_pct` 是负数（约 -5%），说明定价偏低——公司在这类贷款上亏钱了。

**看不懂 SQL？问 AI：**

> "这个 SQL 里的 LEFT JOIN 是什么意思？为什么不用 INNER JOIN？"

> "ROUND(100.0 * COUNT(de.id) / COUNT(l.id), 2) 这个表达式在计算什么？"

> **关键洞察：** SQL 是和数据对话的语言。多跑、多问、多试错，慢慢就熟了。

---

## 核心概念

### 直接字段 vs 计算指标

数据分为两类：

**直接字段**：直接存在表里，SELECT 就能拿到
- `customer.credit_score`
- `loan.outstanding_balance`
- `payment.days_late`

**计算指标（Derived Concepts）**：需要 JOIN 和聚合才能得到
- 实际违约率 = `COUNT(违约) / COUNT(贷款)`
- 定价缺口 = `implied_default_rate - actual_default_rate`
- 逾期率 = `COUNT(days_late > 0) / COUNT(所有还款)`

理解这个区别很重要：
- 直接字段是"事实"
- 计算指标是"洞察"

AI Agent 需要知道如何从事实推导出洞察。这就是为什么我们要花时间学习这些计算指标。

### 15 个关键业务指标

[`database-table-walkthrough-CN.md`](docs/dataset/database-table-walkthrough-CN.md) 文档的"高级分析概念"部分详细介绍了 15 个计算指标：

| 指标 | 业务含义 | 涉及的表 |
|------|---------|---------|
| Actual Default Rate | 实际违约率 | loan, default_event |
| Pricing Gap | 定价差距 | risk_grade, loan, default_event |
| Approval Rate | 审批通过率 | application, loan_status |
| False Rejection | 审批漏失 | application, customer |
| Late Payment Rate | 逾期率 | payment |
| Partial Payment | 部分还款 | payment, loan |
| Recovery Rate | 回收率 | default_event |
| Loss Severity | 损失严重程度 | default_event |
| Expected Loss | 预期损失 | loan, risk_grade |
| Portfolio Concentration | 组合集中度 | loan, customer, industry |
| Days to Decision | 审批周期 | application |
| Payment Behavior Cohort | 还款行为队列 | payment, loan |
| Customer LTV | 客户终身价值 | customer, loan, default_event |
| Vintage Analysis | 年份分析 | loan, default_event |
| Risk Grade Migration | 风险等级迁移 | customer, loan, risk_grade |

每个指标都有公式和 SQL 示例。遇到不理解的，问 AI。

---

## 练习

### 练习 1：探索基础数据

**目标：** 熟悉数据库的基本操作

1. 用 DBeaver 连接 `tmp/data.sqlite`
2. 对每张表运行 `SELECT * FROM <table> LIMIT 5`
3. 用 `SELECT COUNT(*) FROM <table>` 统计每张表的记录数
4. 找到记录数最多的 3 张表

**验证：** repayment_schedule 应该是记录数最多的（约 79,000 条）

---

### 练习 2：探索表关系

**目标：** 理解外键和 JOIN

1. 写一个 SQL，查询所有贷款及其客户名称和所属行业
2. 写一个 SQL，统计每个行业有多少笔贷款

**提示：** 需要 JOIN 三张表：loan, customer, industry

**不会写？问 AI：**

> "帮我写一个 SQL，JOIN loan、customer、industry 三张表，统计每个行业的贷款数量"

---

### 练习 3：计算业务指标

**目标：** 理解计算指标的推导过程

1. 计算整体违约率（所有贷款中违约的比例）
2. 按 risk_grade 分组，计算每个等级的违约率
3. 比较 implied_default_rate 和实际违约率，找出定价缺口

**提示：** 参考文档中 Query 1 的 SQL

---

### 练习 4：自由探索

**目标：** 提出自己的问题，用 SQL 回答

想一个你好奇的业务问题，然后写 SQL 回答它。例如：

- "哪个信贷专员审批的贷款违约率最高？"
- "回头客的平均贷款金额比新客户高多少？"
- "餐饮业的贷款逾期率是不是比科技业高？"

不会写 SQL？用 `/teach-start` 让 AI 帮你。

---

## 回顾：我们学到了什么？

这节课我们深入探索了贷款业务的数据：

**4 份文档，4 个维度：**
1. [`project.README.md`](project.README.md) — 业务背景和 Agent 能力
2. [`database-table-walkthrough-CN.md`](docs/dataset/database-table-walkthrough-CN.md) — 表结构和字段含义
3. [`er_document.md`](docs/dataset/fintech_smb_lending_pipeline_medium_er_document.md) — 表关系和范式化
4. [`sql_queries.md`](docs/dataset/fintech_smb_lending_pipeline_medium_sql_queries.md) — 业务分析 SQL 实战

**核心收获：**
- 数据探索有方法：表结构 → 表关系 → 业务指标
- 直接字段 vs 计算指标的区别
- ER 图是数据库的"地图"
- AI 是你的探索伙伴，不懂就问

**下一步：**
有了数据基础，下节课我们开始看 Agent 的"大脑"——系统提示词。

---

## 导师寄语

**为什么要花这么多时间在数据上？**

我见过很多工程师，拿到需求就开始写代码，然后发现 SQL 写错了、业务逻辑理解偏了、指标算错了。返工的时间比认真探索数据的时间长 10 倍。

**理解数据，就是理解业务。**

当你清楚地知道：
- "违约率怎么算"
- "定价缺口意味着什么"
- "为什么要分析还款行为队列"

你写出来的 Agent 就不只是"能跑"，而是"真的有用"。

**探索数据的过程就是学习业务的过程。**

遇到不懂的概念，问 AI。
写不出 SQL，让 AI 帮你。
不确定结果对不对，和 AI 讨论。

AI 不只是你要构建的产品，也是你学习的伙伴。

**核心洞察：**

- 数据探索不是"准备工作"，是核心技能
- 80% 的 Agent 问题都是"不理解业务"导致的
- 用 AI 加速探索，但要自己验证理解

---

## 快速参考

**数据库连接：**
```
文件路径：tmp/data.sqlite
类型：SQLite
```

**关键文档位置：**
- [`project.README.md`](project.README.md) — 项目概览
- [`docs/dataset/database-table-walkthrough-CN.md`](docs/dataset/database-table-walkthrough-CN.md) — 表结构详解
- [`docs/dataset/fintech_smb_lending_pipeline_medium_er_document.md`](docs/dataset/fintech_smb_lending_pipeline_medium_er_document.md) — ER 图
- [`docs/dataset/fintech_smb_lending_pipeline_medium_sql_queries.md`](docs/dataset/fintech_smb_lending_pipeline_medium_sql_queries.md) — SQL 参考

**常用 SQL 模板：**

```sql
-- 查看表结构
SELECT * FROM <table> LIMIT 5;

-- 统计记录数
SELECT COUNT(*) FROM <table>;

-- 简单聚合
SELECT <column>, COUNT(*) AS cnt
FROM <table>
GROUP BY <column>
ORDER BY cnt DESC;

-- 多表 JOIN
SELECT a.*, b.<column>
FROM <table_a> a
JOIN <table_b> b ON a.<fk> = b.id;
```
