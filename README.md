# SMB Lending Lens: The System Prompt

> Teaching AI to be a domain expert—through a carefully balanced system prompt.

---

## Overview

You've explored the database. You understand the business data. Now comes the question: **how do we teach all of this to an AI?**

The answer is the **system prompt**—a document that transforms a general-purpose LLM into a specialized BI Agent for lending analytics.

This lesson examines a real system prompt and teaches you the art of prompt engineering for AI Agents. It's not about cramming everything in—it's about knowing what to include, what to leave out, and trusting the model to figure out the rest.

---

## Learning Objectives

Why does this matter? Because the system prompt is where your domain expertise meets AI capability. Get it wrong, and your agent is either clueless (too little guidance) or confused (too much information). Get it right, and you unlock an AI that genuinely understands your business.

After completing this lesson, you will:

1. Understand the purpose and structure of an AI Agent system prompt
2. Know what information to include vs. what to let the model discover
3. Recognize the difference between "must-know" concepts and "can-figure-out" details
4. Apply these principles to write system prompts for your own use cases

---

## Prerequisites

- Completed 02-Data-Exploration (database understanding)
- Familiarity with the lending business domain

---

## What You'll Learn

You'll study a production system prompt and understand the design decisions behind it. This is a reading-focused lesson with no coding exercises—the goal is comprehension and insight.

---

## Key Concepts

### The Prompt Engineering Paradox

Here's the core challenge: LLMs are incredibly capable, but they need guidance. Too little guidance, and they hallucinate or miss domain-specific nuances. Too much guidance, and they get overwhelmed, ignore instructions, or lose flexibility.

The art is finding the balance.

**What happens when you include too much:**

- The model gets confused by conflicting or redundant information
- Important instructions get buried in noise
- The model follows the letter of instructions but misses the spirit
- Responses become rigid and formulaic

**What happens when you include too little:**

- The model invents concepts that don't match your business
- It makes reasonable-sounding but incorrect assumptions
- Terminology drifts from your organization's standards
- Critical edge cases get handled incorrectly

The goal is to provide **just enough** structure while trusting the model's underlying capabilities.

### The System Prompt Structure

A well-designed system prompt has four layers:

**1. Identity and Scope**

Tell the model who it is and what it can/cannot do. This sets boundaries.

```
You are SMB Lending Lens BI Agent, a read-only database assistant...
```

**2. Core Domain Concepts**

Explain the fundamental business concepts the model must understand. These are the "rules of the game" that don't change.

- The lending lifecycle (Customer → Application → Loan → Payments)
- Risk grading system (what grades mean, how pricing works)
- Key terminology (what "default" means in this context)

**3. Derived Business Concepts**

These are calculated metrics that require specific formulas. The model might guess wrong if you don't specify them.

- Actual Default Rate = COUNT(defaults) / COUNT(loans)
- Pricing Gap = implied_default_rate - actual_default_rate
- Late Payment Rate = COUNT(days_late > 0) / COUNT(payments)

**4. Technical Patterns**

SQL patterns, gotchas, and domain-specific conventions.

- How to avoid SQLite integer division bugs
- When to use LEFT JOIN vs INNER JOIN
- Output formatting standards

### What to Include vs. What to Omit

This is where experience matters. Here's a framework:

**Must Include (the model can't figure this out):**

- Business-specific terminology and definitions
- Calculated metrics with exact formulas
- Domain rules that differ from common assumptions
- Table relationships that aren't obvious from names

**Can Omit (trust the model):**

- Basic SQL syntax (the model knows SQL)
- General database concepts (joins, aggregations)
- Common sense reasoning about data
- Exploratory analysis techniques

**Example: Pricing Gap**

The model knows what "default rate" means generally. But it doesn't know:

- That your company uses "implied_default_rate" for pricing
- That comparing implied vs actual reveals mispricing
- That negative gap = underpriced = losing money

So you must define "Pricing Gap" explicitly. But you don't need to explain what subtraction is.

### The Tools Layer

The system prompt also defines available tools:

1. **get_database_schema** — Let the model explore structure
2. **execute_sql_query** — Run queries and get results
3. **write_debug_report** — Document reasoning

Notice what's NOT here: there's no "get_all_table_relationships" or "explain_business_context" tool. Why? Because that information is already in the prompt where the model can reference it instantly.

Tools are for runtime data access. The prompt is for domain knowledge.

### Examples: Just Enough, Not Too Much

Look at how the system prompt handles risk grades:

```
| Grade | Credit Score Range | Interest Rate | Implied Default Rate |
|-------|-------------------|---------------|---------------------|
| A (Prime) | 720-850 | 5.5% | 3.0% |
| B (Near Prime) | 680-719 | 7.5% | 6.0% |
...
```

This table is included because:

- The model can't know your specific grade boundaries
- The implied default rates are business decisions, not derivable
- This information is used frequently in analysis

But the prompt doesn't explain what a credit score is, or how interest rates work, or what "prime" means in lending. The model already knows those things.

### SQL Patterns: Teaching by Example

The prompt includes SQL examples for each derived metric. Why?

Because showing is more effective than telling. Instead of writing:

> "When calculating default rate, divide the count of default events by the count of loans, multiply by 100, and use 1.0 or 100.0 to force floating-point division in SQLite..."

You write:

```sql
SELECT ROUND(100.0 * COUNT(de.id) / COUNT(l.id), 2) AS actual_default_rate
FROM loan l
LEFT JOIN default_event de ON l.id = de.loan_id
```

The example teaches:

- The exact formula
- The SQLite float trick (100.0 instead of 100)
- The LEFT JOIN pattern for optional relationships
- The naming convention (actual_default_rate)

All without verbose explanation.

### Safety and Boundaries

The prompt includes safety constraints:

```
- **Read-only**: Only SELECT queries allowed
- Never attempt UPDATE, INSERT, DELETE, or DROP
```

This is critical. You're giving an AI access to your database. Clear boundaries prevent disasters.

But notice what's NOT here: there's no long explanation of why this matters, no threat assessment, no security policy document. Just clear rules.

---

## Reading the System Prompt

Now open the actual system prompt and read it with these concepts in mind:

**File:** [learn_smb_lending_lens/prompts/bi-agent-system-prompt.md](learn_smb_lending_lens/prompts/bi-agent-system-prompt.md)

As you read, ask yourself:

1. **Identity:** How does the prompt define who the agent is?
2. **Domain concepts:** What business knowledge is explicitly taught?
3. **Derived metrics:** Which calculations are spelled out with formulas?
4. **Technical patterns:** What SQL patterns and gotchas are documented?
5. **Omissions:** What does the prompt trust the model to figure out?

Pay special attention to the "Derived Business Concepts" section. Each metric has:

- A name
- A formula
- A SQL example

This is the template for encoding domain expertise.

---

## Reflection: The Art of Balance

Writing a system prompt is like writing documentation for a very smart but very new team member:

- They're intelligent and capable
- They learn fast from examples
- They need to know your specific terminology
- They don't need basic concepts re-explained
- They'll fill in gaps with reasonable assumptions (which may be wrong)

Your job is to give them just enough to be effective without overwhelming them.

**Signs your prompt is too long:**

- Instructions get ignored
- Behavior becomes inconsistent
- The model seems "confused" about priorities

**Signs your prompt is too short:**

- The model invents non-standard terminology
- Calculations don't match your expectations
- Edge cases are handled incorrectly

There's no perfect prompt. Iteration is expected. Start with what you think is essential, test it, observe failures, and adjust.

---

## Mentor's Note

**Why this lesson matters:**

System prompts are where human expertise meets AI capability. Anyone can call an LLM API. But building an AI Agent that truly understands your domain—that requires the skill of knowledge transfer.

This skill will become increasingly valuable. As AI tools proliferate, the differentiator won't be "can you use AI?" but "can you teach AI to do your job?"

**Key insights:**

- Less is often more. Trust the model's baseline capabilities.
- Calculated metrics need exact definitions. Business logic can't be guessed.
- Show, don't tell. SQL examples beat verbose explanations.
- Clear boundaries prevent disasters. Safety rules should be explicit.
- There's no perfect prompt. Expect iteration.

**A personal observation:**

I've seen engineers dump entire documentation sets into system prompts, thinking more information equals better performance. It doesn't. The model gets lost. The signal drowns in noise.

The best prompts I've written are surprisingly short. They focus on what makes THIS domain unique, and trust the model for everything else.

Think of it like briefing an expert consultant. You don't explain accounting basics to a CPA. You explain YOUR chart of accounts, YOUR reporting conventions, YOUR edge cases. That's the mindset for system prompt design.

---

## Quick Reference

**System Prompt Location:**
```
learn_smb_lending_lens/prompts/bi-agent-system-prompt.md
```

**Prompt Structure:**

- Identity and scope (who is the agent, what can it do)
- Core domain concepts (business fundamentals)
- Derived metrics (calculated values with formulas)
- Technical patterns (SQL idioms, gotchas)
- Safety boundaries (what's forbidden)

**The Balance Rule:**

- Include: Business-specific definitions, calculated metrics, domain rules
- Omit: Basic concepts the model already knows

**Design Questions:**

- "Would a smart new hire need this explained?"
- "Could the model reasonably guess wrong?"
- "Is this a rule or a derivable fact?"
