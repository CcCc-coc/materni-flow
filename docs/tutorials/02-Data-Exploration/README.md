# SMB Lending Lens: Data Exploration

> Understanding business data is the foundation of building any AI Agent. This lesson takes you deep into the lending database.

---

## Overview

Last lesson, we covered the AI Agent framework: Database + Tools + Prompt + Context + Workflow.

This lesson, we fill in the blanks—by deeply understanding the data.

**Why does this matter?**

Imagine you just joined a new company. Your boss says, "Analyze our loan data." You open the database and see 10 tables, tens of thousands of records. Where do you even start?

The answer: **explore systematically**.

That's what this lesson teaches. You'll:
- Read 4 documents that map out the data landscape
- Connect to the database with DBeaver and run SQL hands-on
- Ask AI whenever you get stuck

**AI is your exploration partner.** Can't write SQL? Ask AI. Don't understand a field? Ask AI. Want to test a hypothesis? Let AI write the query for you.

---

## Learning Objectives

After completing this lesson, you will:

1. Master a methodology for exploring unfamiliar databases
2. Understand the complete lending business data flow
3. Read ER diagrams and understand table relationships
4. Know 15+ key business metrics and how to calculate them
5. Answer basic business questions with SQL

---

## Prerequisites

- Basic SQL (SELECT, JOIN, GROUP BY, WHERE)
- Completed 01-Project-Overview
- DBeaver installed (or another database client)

---

## Reading Guide

This lesson is about **reading + exploring**. You'll work through 4 documents in sequence, validating what you read with hands-on SQL.

**Important:** Whenever you hit something you don't understand, **ask AI immediately**. Use `/teach-start` to enter interactive mode—AI will help you understand concepts, write SQL, and interpret results.

---

### Step 1: Understand the Business Context

**Document:** [`project.README.md`](project.README.md)

**Goal:** Understand what business problems this project solves

**Key questions to answer:**

1. What is Pacific Bridge Lending?
2. What 5 types of analysis can the AI Agent perform?
3. How many tables are in the database? What business process do they cover?

**What you'll see:**

```
Business Customer → Submit Application → Credit Review → Disburse Loan → Monthly Payments → Paid Off / Default
```

This is the entire business data flow. Every table you'll encounter maps to a stage in this pipeline.

> **Key insight:** Data mirrors business. Understand the business flow, and the schema makes sense.

---

### Step 2: Deep Dive into Table Structure

**Document:** [`docs/dataset/database-table-walkthrough.md`](docs/dataset/database-table-walkthrough.md) (or the English version if available)

**Goal:** Understand what each table stores and what the fields mean

**This is the most important step!**

The document walks through 10 tables organized by dependency:

| Tier | Tables | Description |
|------|--------|-------------|
| Tier 1 | industry, risk_grade, loan_status, loan_officer | Config/lookup tables, no dependencies |
| Tier 2 | customer | Core entity, depends on industry |
| Tier 3 | application, loan | Business process tables |
| Tier 4 | repayment_schedule, payment, default_event | Transaction detail tables |

**Hands-on exploration:**

1. Open DBeaver and connect to `tmp/data.sqlite`
2. For each table, run:

```sql
-- See what's in the table
SELECT * FROM industry LIMIT 5;

-- Count records
SELECT COUNT(*) FROM industry;
```

3. Can't write SQL? Ask AI:

> "Write a SQL query to show the first 10 customers with their industry names"

AI will give you:

```sql
SELECT c.*, i.industry_name
FROM customer c
JOIN industry i ON c.industry_id = i.id
LIMIT 10;
```

**Pay special attention to:**

- `risk_grade.implied_default_rate` — the default rate assumed during pricing
- `customer.is_repeat_customer` — whether they've borrowed before
- `payment.days_late` — how many days past due
- `default_event.had_early_warning` — whether warning signs existed

These fields are critical for business analysis.

> **Key insight:** Don't try to memorize every field. Build a mental map first, reference docs when needed.

---

### Step 3: Understand Table Relationships

**Document:** [`docs/dataset/fintech_smb_lending_pipeline_medium_er_document.md`](docs/dataset/fintech_smb_lending_pipeline_medium_er_document.md)

**Goal:** Learn to read ER diagrams and understand foreign key relationships

**What's an ER Diagram?**

An ER (Entity-Relationship) diagram visualizes how tables connect.

```
customer ||--o{ application : "submits"
```

This means: one customer can submit multiple applications (one-to-many relationship).

**Key concept: Normalization vs Denormalization**

You might notice that the `loan` table has both `application_id` and `customer_id`. Technically, you could get `customer_id` through the application table. Why store it redundantly?

This is **denormalization**.

- **Normalization:** No redundant data, use JOINs to query
- **Denormalization:** Store redundantly for query performance

`loan.customer_id` is redundant, but it eliminates one JOIN in many common queries.

**Ask AI if confused:**

> "What does the `||--o{` symbol mean in ER diagrams?"

> "Why does the loan table store both application_id and customer_id?"

**Hands-on validation:**

```sql
-- Verify application -> loan is 1:1
SELECT application_id, COUNT(*)
FROM loan
GROUP BY application_id
HAVING COUNT(*) > 1;
-- Empty result = confirmed 1:1

-- Verify customer -> loan is 1:N
SELECT customer_id, COUNT(*) AS loan_count
FROM loan
GROUP BY customer_id
ORDER BY loan_count DESC
LIMIT 5;
-- See how many loans the top customer has
```

> **Key insight:** The ER diagram is your database "map." Before writing complex queries, trace the JOIN path on the diagram.

---

### Step 4: Learn Business Metrics and SQL

**Document:** [`docs/dataset/fintech_smb_lending_pipeline_medium_sql_queries.md`](docs/dataset/fintech_smb_lending_pipeline_medium_sql_queries.md)

**Goal:** Study 20 real-world SQL queries and understand business analysis patterns

**This is the most technical step!**

The document contains 20 business queries, each with:
- Business context (why this analysis matters)
- SQL code
- Expected results explanation

**Recommended reading order:**

1. **Query 1: Risk Pricing Analysis** — Core analysis Q1
2. **Query 2: Portfolio Concentration** — Core analysis Q2
3. **Query 5: Customer Lifecycle Value** — Core analysis Q5
4. **Query 8: Payment Behavior Cohort** — Learn CTEs (Common Table Expressions)
5. Other queries that interest you

**Run the queries:**

Open DBeaver, copy SQL from the document, and execute it.

For example, Query 1 (Risk Pricing Analysis):

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

After running, you'll see Grade C loans have a negative `pricing_gap_pct` (about -5%). This means they're underpriced—the company loses money on these loans.

**Don't understand the SQL? Ask AI:**

> "What does LEFT JOIN mean in this SQL? Why not use INNER JOIN?"

> "What is ROUND(100.0 * COUNT(de.id) / COUNT(l.id), 2) calculating?"

> **Key insight:** SQL is the language for talking to data. Run queries, ask questions, make mistakes—that's how you learn.

---

## Core Concepts

### Direct Fields vs Derived Metrics

Data comes in two forms:

**Direct fields:** Stored in tables, retrieved with SELECT
- `customer.credit_score`
- `loan.outstanding_balance`
- `payment.days_late`

**Derived metrics:** Calculated through JOINs and aggregation
- Actual Default Rate = `COUNT(defaults) / COUNT(loans)`
- Pricing Gap = `implied_default_rate - actual_default_rate`
- Late Payment Rate = `COUNT(days_late > 0) / COUNT(all_payments)`

This distinction matters:
- Direct fields are "facts"
- Derived metrics are "insights"

AI Agents need to know how to derive insights from facts. That's why we spend time learning these calculations.

### 15 Key Business Metrics

The "Advanced Analysis Concepts" section in [`database-table-walkthrough-CN.md`](docs/dataset/database-table-walkthrough-CN.md) covers 15 derived metrics:

| Metric | Business Meaning | Tables Involved |
|--------|------------------|-----------------|
| Actual Default Rate | Real default percentage | loan, default_event |
| Pricing Gap | Difference from pricing assumption | risk_grade, loan, default_event |
| Approval Rate | Applications approved | application, loan_status |
| False Rejection | Good customers wrongly rejected | application, customer |
| Late Payment Rate | Payments past due | payment |
| Partial Payment | Underpayments | payment, loan |
| Recovery Rate | Amount recovered after default | default_event |
| Loss Severity | Loss as % of exposure | default_event |
| Expected Loss | Projected loss amount | loan, risk_grade |
| Portfolio Concentration | Industry exposure % | loan, customer, industry |
| Days to Decision | Application processing time | application |
| Payment Behavior Cohort | Grouping by payment patterns | payment, loan |
| Customer LTV | Lifetime value comparison | customer, loan, default_event |
| Vintage Analysis | Performance by origination period | loan, default_event |
| Risk Grade Migration | Customers qualifying for better rates | customer, loan, risk_grade |

Each metric has a formula and SQL example. Ask AI when you need clarification.

---

## Exercises

### Exercise 1: Explore Basic Data

**Goal:** Get comfortable with database operations

1. Connect to `tmp/data.sqlite` with DBeaver
2. Run `SELECT * FROM <table> LIMIT 5` for each table
3. Run `SELECT COUNT(*) FROM <table>` to count records
4. Find the 3 tables with the most records

**Verification:** repayment_schedule should have the most records (~79,000)

---

### Exercise 2: Explore Relationships

**Goal:** Understand foreign keys and JOINs

1. Write SQL to list all loans with customer names and industries
2. Write SQL to count loans per industry

**Hint:** You'll need to JOIN three tables: loan, customer, industry

**Stuck? Ask AI:**

> "Write a SQL query joining loan, customer, and industry tables to count loans by industry"

---

### Exercise 3: Calculate Business Metrics

**Goal:** Understand how derived metrics are computed

1. Calculate the overall default rate (defaults / total loans)
2. Group by risk_grade and calculate default rate per grade
3. Compare implied_default_rate vs actual default rate to find pricing gaps

**Hint:** Reference Query 1 from the SQL document

---

### Exercise 4: Free Exploration

**Goal:** Ask your own questions and answer them with SQL

Think of a business question you're curious about, then write SQL to answer it. Examples:

- "Which loan officer has the highest default rate on approved loans?"
- "Do repeat customers borrow more than first-time customers on average?"
- "Is the late payment rate higher for restaurants than for tech companies?"

Can't write the SQL? Use `/teach-start` and let AI help.

---

## Reflection: What Did We Learn?

This lesson took us deep into the lending business data:

**4 Documents, 4 Dimensions:**
1. [`project.README.md`](project.README.md) — Business context and Agent capabilities
2. [`database-table-walkthrough-CN.md`](docs/dataset/database-table-walkthrough-CN.md) — Table structure and field meanings
3. [`er_document.md`](tmp/fintech_smb_lending_pipeline_medium_er_document.md) — Table relationships and normalization
4. [`sql_queries.md`](docs/dataset/fintech_smb_lending_pipeline_medium_sql_queries.md) — Business SQL in action

**Key takeaways:**
- Data exploration has a method: structure → relationships → metrics
- Direct fields vs derived metrics distinction
- ER diagrams are the database "map"
- AI is your exploration partner—ask whenever stuck

**What's next:**
With the data foundation in place, next lesson we'll look at the Agent's "brain"—the system prompt.

---

## Mentor's Note

**Why spend so much time on data?**

I've seen engineers jump straight into coding, then discover their SQL is wrong, their business logic is off, their metrics are miscalculated. The rework takes 10x longer than careful data exploration would have.

**Understanding data means understanding business.**

When you clearly know:
- "How to calculate default rate"
- "What pricing gap means"
- "Why we analyze payment behavior cohorts"

The Agent you build won't just "work"—it will be genuinely useful.

**Data exploration IS business learning.**

Confused about a concept? Ask AI.
Can't write SQL? Let AI help.
Not sure if results are correct? Discuss with AI.

AI isn't just the product you're building—it's also your learning partner.

**Key insights:**

- Data exploration isn't "prep work"—it's a core skill
- 80% of Agent failures trace back to misunderstanding the business
- Use AI to accelerate exploration, but verify understanding yourself

---

## Quick Reference

**Database connection:**
```
File path: tmp/data.sqlite
Type: SQLite
```

**Key document locations:**
- [`project.README.md`](project.README.md) — Project overview
- [`docs/dataset/database-table-walkthrough.md`](docs/dataset/database-table-walkthrough.md) — Table structure details
- [`docs/dataset/fintech_smb_lending_pipeline_medium_er_document.md`](tmp/fintech_smb_lending_pipeline_medium_er_document.md) — ER diagram
- [`docs/dataset/fintech_smb_lending_pipeline_medium_sql_queries.md`](docs/dataset/fintech_smb_lending_pipeline_medium_sql_queries.md) — SQL reference

**Common SQL templates:**

```sql
-- View table structure
SELECT * FROM <table> LIMIT 5;

-- Count records
SELECT COUNT(*) FROM <table>;

-- Simple aggregation
SELECT <column>, COUNT(*) AS cnt
FROM <table>
GROUP BY <column>
ORDER BY cnt DESC;

-- Multi-table JOIN
SELECT a.*, b.<column>
FROM <table_a> a
JOIN <table_b> b ON a.<fk> = b.id;
```
