# MaterniFlow

MaterniFlow is a conversational operations console for a simulated obstetrics ward. It turns a ward snapshot into a shared handover: which beds are ready, who is on the floor, which alerts need attention, and what procedures are scheduled next. The interface is designed for the few minutes between shifts, when a clear answer matters more than another dashboard.

## What it does

Ask questions in plain English and receive answers grounded in a PostgreSQL dataset with 11 tables and 355 synthetic records. MaterniFlow covers shift handover, bed capacity, risk monitoring, and care scheduling. Answers can be returned as readable summaries or rendered as tables, charts, and handover flows.

## Run locally

Requirements: Python 3.12, `uv`, Node.js, `pnpm`, and PostgreSQL.

```bash
cp .env.example .env
mise run inst
mise run dev
```

The web app runs on port 3000 and the API on port 8000. Configure the database connection and model credentials in `.env` before asking a question.

## How it works

The Python service reflects the active PostgreSQL schema, encodes it for the model, and exposes a read-only SQL tool. The Next.js app streams the agent response through a rendering contract: ordinary Markdown stays readable, while fenced table, chart, and diagram blocks become visual components.

Domain knowledge lives in the content layer while application boundaries stay stable. The prompt, site copy, and schema can describe a new operational domain without rewriting chat transport, rendering, or database safety rules. SQL runs inside a transaction that is always rolled back, making read-only behavior a runtime property rather than a prompt promise.

## Stack

- Next.js and TypeScript
- FastAPI and Python
- PostgreSQL
- Strands SDK

## Next step

Connect MaterniFlow to a live scheduling feed and add role-specific handover views while keeping synthetic data available for safe demos and regression tests.
