# Ticket: 03-The-System-Prompt

## Objective

Study how to write an effective AI Agent system prompt by comparing a production prompt against its source materials. Understand what to include, what to omit, and why.

Read the tutorial: [SMB Lending Lens - The System Prompt](https://github.com/easyscale-academy/learn_smb_lending_lens-project/tree/03-The-System-Prompt/)

---

## Actionable Items

### 1. Read the System Prompt

Study the actual system prompt used by the BI Agent:

**File:** [`learn_smb_lending_lens/prompts/bi-agent-system-prompt.md`](learn_smb_lending_lens/prompts/bi-agent-system-prompt.md)

As you read, identify:
- Identity and scope (who is the agent?)
- Core domain concepts (business fundamentals)
- Derived metrics (calculated values with formulas)
- Technical patterns (SQL idioms, gotchas)
- Safety boundaries (what's forbidden)

### 2. Compare with Source Documents

The system prompt is a **condensed version** of these reference documents:

1. `docs/dataset/fintech_smb_lending_pipeline_medium_er_document.md` — Full ER diagram and table definitions
2. `docs/dataset/fintech_smb_lending_pipeline_medium_sql_queries.md` — 20 business SQL queries with context

**Key exercise:** For each section in the system prompt, find the corresponding content in the source documents. Ask yourself:
- What was **kept**? Why?
- What was **removed**? Why?
- What was **simplified**? How?

### 3. Understand the Balance

Focus on these key concepts:

- **Must include:** Business-specific definitions, calculated metrics, domain rules
- **Can omit:** Basic SQL, general database concepts, common sense reasoning
- **Design question:** "Would a smart new hire need this explained?"

### 4. Use /teach-start for Guided Reading

Run `/teach-start` to have AI guide you through the comparison. The AI will help you:
- Navigate between the prompt and source documents
- Explain why certain information was included or excluded
- Answer questions about prompt engineering decisions

**Estimated time:** 30-45 minutes

---

## Checklist

- [ ] **System prompt read** — Read the entire system prompt and identified its structure
- [ ] **Source documents reviewed** — Skimmed both ER document and SQL queries document
- [ ] **Comparison done** — Compared at least 3 sections between prompt and source
- [ ] **Balance understood** — Can explain what to include vs. omit in a system prompt

---

## Submission & Verification

When you're done, run `/teach-check` to verify your work against the checklist. Say "ship it" when complete to generate RESULT.md, then share the RESULT.md file GitHub link with your instructor.

---

## Grading Rubric

> **For instructors and /teach-check assistant** — Students may skip this section.

### Minimum Requirements

- **Prompt comprehension**: Student has read the system prompt and can identify its sections
- **Comparison exercise**: Student has compared prompt content against source documents
- **Design principles**: Student can explain the "balance" concept in prompt engineering

### Knowledge Check Questions

Ask students to explain:

1. **Q:** What are the 4 main sections of a well-designed system prompt?
   **A:** (1) Identity and scope, (2) Core domain concepts, (3) Derived metrics with formulas, (4) Technical patterns and safety boundaries.

2. **Q:** The system prompt has a Risk Grade table. Why is this included instead of letting the model figure it out?
   **A:** The model can't know company-specific grade boundaries or implied default rates (business decisions). This information is used frequently and can't be derived from table names.

3. **Q:** The source SQL document has 20 queries with detailed business context. The system prompt has much shorter examples. Why?
   **A:** The prompt keeps only the essential formulas and patterns. Verbose business context is noise—the model already understands general business reasoning. Show, don't tell.

4. **Q:** What's the "pricing gap" formula, and why must it be explicitly defined?
   **A:** Pricing gap = implied_default_rate - actual_default_rate. It must be defined because (1) the model doesn't know your company uses "implied_default_rate" for pricing, (2) negative gap = underpriced = losing money is a business interpretation.

5. **Q:** Pick one section from the system prompt. What was removed compared to the source document?
   **A:** Example: The ER diagram section in source has full CREATE TABLE DDL, sample data, faker strategies. The prompt has only table relationships in simple format (e.g., "customer.id → loan.customer_id") because the model already knows SQL and can query the schema.

### Assessment Ideas

- Ask student to pick a derived metric and trace it back to the source SQL query
- Ask student to explain why the prompt doesn't include a full explanation of what "credit score" means
- Ask student to identify one thing they would add or remove from the prompt
