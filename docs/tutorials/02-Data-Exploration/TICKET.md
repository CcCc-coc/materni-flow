# Ticket: 02-Data-Exploration

## Objective

Explore the lending database systematically and build a deep understanding of the business data model.

Read the tutorial: [SMB Lending Lens - Data Exploration](https://github.com/easyscale-academy/agent_app-project/tree/02-Data-Exploration/)

---

## Actionable Items

### 1. Read the 4 Documents

Work through these documents in order, using `/teach-start` for AI assistance:

1. [`project.README.md`](project.README.md) — Business context
2. [`docs/dataset/database-table-walkthrough.md`](docs/dataset/database-table-walkthrough.md) — Table structures
3. [`docs/dataset/fintech_smb_lending_pipeline_medium_er_document.md`](docs/dataset/fintech_smb_lending_pipeline_medium_er_document.md) — ER diagram
4. [`docs/dataset/fintech_smb_lending_pipeline_medium_sql_queries.md`](docs/dataset/fintech_smb_lending_pipeline_medium_sql_queries.md) — Business SQL queries

### 2. Hands-on SQL Exploration

Connect to `tmp/data.sqlite` with DBeaver and run queries:

- View sample data from each table
- Count records in each table
- Run at least 3 queries from the SQL document

### 3. Understand Key Concepts

Make sure you can explain:

- The 4-tier table dependency structure
- Direct fields vs derived metrics
- What "pricing gap" means in this business context

### 4. Complete the Exercises

Work through the 4 exercises in the README. Use `/teach-start` if you need help.

**Estimated time:** 60-90 minutes

---

## Checklist

- [ ] **Documents read** — Read all 4 documents (project.README.md, table walkthrough, ER diagram, SQL queries)
- [ ] **Database connected** — Connected to tmp/data.sqlite with DBeaver
- [ ] **SQL executed** — Ran at least 5 queries manually
- [ ] **Table structure understood** — Can explain the 4-tier dependency structure
- [ ] **Derived metrics understood** — Can explain what "pricing gap" and "actual default rate" mean

---

## Submission & Verification

When you're done, run `/teach-check` to verify your work against the checklist. Say "ship it" when complete to generate RESULT.md, then share the RESULT.md file GitHub link with your instructor.

---

## Grading Rubric

> **For instructors and /teach-check assistant** — Students may skip this section.

### Minimum Requirements

- **Document comprehension**: Student has read all 4 documents and can summarize their purpose
- **Hands-on experience**: Student has connected to the database and run queries
- **Concept understanding**: Student can explain table dependencies and derived metrics

### Knowledge Check Questions

Ask students to explain:

1. **Q:** What are the 4 tiers of tables in this database, and what's in each tier?
   **A:** Tier 1: Config tables (industry, risk_grade, loan_status, loan_officer) — no dependencies. Tier 2: customer — depends on industry. Tier 3: application, loan — business process. Tier 4: repayment_schedule, payment, default_event — transaction details.

2. **Q:** What is the difference between a direct field and a derived metric?
   **A:** Direct fields are stored in tables (e.g., credit_score). Derived metrics are calculated through JOINs and aggregation (e.g., default_rate = COUNT(defaults) / COUNT(loans)).

3. **Q:** What is "pricing gap" and why does it matter?
   **A:** Pricing gap = implied_default_rate - actual_default_rate. Negative gap means underpriced (actual defaults exceed assumption, company loses money). Positive gap means overpriced (may lose customers to competitors).

4. **Q:** Why does the loan table have both application_id and customer_id?
   **A:** Denormalization for query performance. customer_id is technically redundant (could be derived through application), but storing it directly eliminates one JOIN in common queries.

### Assessment Ideas

- Ask student to show their DBeaver connection and run a query live
- Ask student to explain the ER diagram relationships
- Ask student to calculate default rate by risk grade and explain what they see
