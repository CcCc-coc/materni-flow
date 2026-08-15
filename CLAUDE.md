## Context Files

- Role & Behavior: @.claude/MENTOR.md
- Tutorial: @README.md
- Task Card: @TICKET.md

## Code Architecture

### Entry Point

```python
from agent_app.api import one  # Main singleton instance
```

### Directory Structure

```
config/                      # Committed to Git. Split by CONSUMER, not by topic.
├── site.ts                  #   Everything the frontend says. TypeScript, typed.
└── dataset.toml             #   The 4 values Python reads. TOML, commented.

agent_app/                   # Python package. Name is deliberately generic and
├── api.py                   #   never changes when the dataset changes.
├── paths.py
├── project_config.py        # Typed reader over config/*.json
├── runtime.py
├── constants.py
├── sql_utils.py
├── ai_sdk_adapter.py
│
├── config/                  # NOTE: secrets from .env -- NOT config/*.json
│   └── conf_00_def.py
│
├── one/
│   ├── one_00_main.py
│   ├── one_01_config.py
│   ├── one_02_db.py
│   ├── one_03_boto3.py
│   ├── one_04_agent.py
│   └── api.py
│
├── prompts/
│   └── bi-agent-system-prompt.md
│
└── db_schema/

lib/
├── icons.ts                 # Icon-name -> component map; exports the IconName type
└── constants.ts             # Derived view of config/site.ts; authored nothing
```

### The Two Kinds of "Config"

Two things in this repo are called config. They change for different reasons and
must not be mixed:

| | `config/site.ts` + `config/dataset.toml` | `.env` → `agent_app/config/` |
|---|---|---|
| Holds | Project identity, business copy, table order | API keys, DB credentials, LLM provider |
| Differs per | **dataset** | **machine** |
| In Git | Yes | No |
| Read by | Next.js *and* Python | Python only |

Rotating an API key must not touch the project's name; pointing the repo at a
new dataset must not touch anyone's credentials.

**The test for which layer a value belongs to: does it vary by environment?**
`agent_app/project_config.py` reads `config/dataset.toml` and nothing in it
varies by environment. Local, Vercel, and CI all serve the same dataset, so they
all get the same answer. `agent_app/config/conf_00_def.py` holds everything that
*does* differ per machine. A value must not appear in both, not even with an
environment variable as an "escape hatch": that gives it two homes and
eventually two answers. `project_name` used to be duplicated that way and is
now only in `project_config`.

**`config/` is split by consumer, not by topic.** The frontend and the backend
read disjoint sets of keys, so one shared file was two unrelated files stapled
together. `site.ts` is TypeScript because only TypeScript reads it, which buys
autocomplete and makes a bad icon name a compile error. `dataset.toml` is TOML
because only Python reads it, and TOML has real comments. Before adding a value,
ask which runtime consumes it; if the answer is "both", say so out loud, because
today nothing does.

**Comments and identifiers are English only.** Every comment, docstring, and
name in the source tree (`.ts`, `.tsx`, `.py`) is written in English, even when
the conversation that produced it was in Chinese. Chinese belongs in
`.claude/skills/*-cn/` docs and in chat, never in code. Mixed-language comments
make the codebase unreadable for anyone who joins later and unsearchable by
keyword.

**No author identity anywhere.** This site presents a product, not a person.
There is no name, photo, contact link, or `author`/`creator` page metadata, and
none should be added — that was portfolio scaffolding the app inherited and does
not need.

### Swapping the Dataset

Everything that varies between datasets is either in `config/` or in one of
three content files. When adding UI copy, a brand string, or a business term,
put it in `config/site.ts` — never inline it in a component.

| What | Where |
|---|---|
| Product name, all UI copy, SEO, icons | `config/site.ts` |
| Table prefix, DB display name, table order, prompt file | `config/dataset.toml` |
| Agent's domain knowledge | `agent_app/prompts/bi-agent-system-prompt.md` |
| Kickstart questions | `data/suggested-actions.json` |
| The data itself | `data.sqlite.example` |
| Dataset-specific write tools | `@tool` methods in `one_04_agent.py` |

Run `mise run check` afterwards. It fails on a `tableInsertOrder` that
disagrees with the SQLite file, a prompt that queries a nonexistent table, and
missing content files. Right after a swap also run it with the outgoing
domain's vocabulary, which is a one-off argument rather than committed state:

```bash
mise run check -- --retired "patient,bed,ward,nurse"
```

Icon names need no check: `config/site.ts` types them against `lib/icons.ts`, so
a typo is a compile error.

### When to Modify Each File

**Root Level Modules:**

| File | What It Does | When to Modify |
|------|--------------|----------------|
| `api.py` | Re-exports `one` singleton | Rarely. Only if you need to expose additional top-level imports. |
| `paths.py` | Defines all file/directory paths as `PathEnum`, including the system prompt | When adding new files (prompts, data files, output paths). Add path here first, then use `path_enum.your_new_path` everywhere. Paths are source-tree facts, so they are never named in config. |
| `runtime.py` | Detects runtime environment (local vs vercel) | When adding a new deployment target (e.g., AWS Lambda). Add new enum value and detection logic. |
| `constants.py` | Enums and constants | When adding new enum types or magic values that need to be shared across modules. |
| `project_config.py` | Typed reader over `config/dataset.toml`; also owns the `project_name` derivations (`_snake`, `_slug`, `prefix_table_name`) | When Python needs a new dataset value. If it varies by environment it belongs in `config/conf_00_def.py`; if only the frontend reads it, `config/site.ts`. |
| `sql_utils.py` | Pure functions for SQL execution and formatting | When changing how SQL results are formatted or adding new query validation rules. |
| `ai_sdk_adapter.py` | Converts Vercel AI SDK format <-> Bedrock format | When frontend message format changes or when switching to a different LLM provider. |

**config/ Directory:**

| File | What It Does | When to Modify |
|------|--------------|----------------|
| `conf_00_def.py` | Config dataclass with env vars, credentials, settings | When adding new environment variables (add field + load in `new_in_local_runtime()` and `new_in_vercel_runtime()`). |

**one/ Directory (Main Class + Mixins):**

| File | What It Does | When to Modify |
|------|--------------|----------------|
| `one_00_main.py` | Defines `One` class that inherits all mixins; creates `one` singleton | When adding a new mixin (import it and add to inheritance list). |
| `one_01_config.py` | `ConfigMixin`: provides `self.config` | Rarely. Config loading logic is in `conf_00_def.py`. |
| `one_02_db.py` | `DbMixin`: provides `self.engine`, `self.local_sqlite_engine`, `self.remote_postgres_engine` | When adding new database connections or changing engine selection logic. |
| `one_03_boto3.py` | `Boto3Mixin`: provides `self.boto_ses`, `self.bedrock_runtime_client()` | When adding new AWS service clients (S3, DynamoDB, etc.). |
| `one_04_agent.py` | `AgentMixin`: provides `self.agent` and all `@tool` methods | **Most common edit.** When adding/modifying agent tools. Add `@tool` method here, then register in `self.agent`'s `tools=[]` list. |
| `api.py` | Exports `one = One()` singleton | Rarely. Only touched when restructuring exports. |

**prompts/ Directory:**

| File | What It Does | When to Modify |
|------|--------------|----------------|
| `bi-agent-system-prompt.md` | System prompt for the BI agent | When changing agent behavior, adding tool usage instructions, or updating workflow guidelines. |

**db_schema/ Directory:**

| File | What It Does | When to Modify |
|------|--------------|----------------|
| (multiple files) | Extracts and encodes database schema in LLM-optimized format | When changing schema representation format or adding support for new database types. |

### Class Hierarchy

```
One (one_00_main.py)
├── ConfigMixin (one_01_config.py)
│   └── self.config -> Config instance (from conf_00_def.py)
│
├── DbMixin (one_02_db.py)
│   ├── self.local_sqlite_engine   -> SQLite (tmp/data.sqlite)
│   ├── self.remote_postgres_engine -> PostgreSQL (NeonDB)
│   ├── self.engine                -> Auto-selects based on runtime
│   ├── self.database_schema_str   -> LLM-optimized schema string
│   └── self.execute_and_print_result(sql) -> Markdown table
│
├── Boto3Mixin (one_03_boto3.py)
│   ├── self.boto_ses              -> boto3.Session
│   └── self.bedrock_runtime_client() -> BedrockRuntimeClient
│
└── AgentMixin (one_04_agent.py)
    ├── self.bedrock_model         -> BedrockModel (strands)
    ├── self.agent                 -> Agent with tools
    └── @tool methods:
        ├── tool_get_database_schema
        ├── tool_execute_sql_query
        └── tool_write_debug_report
```

### Pure Functions vs Bound Methods

| Type | Location | Characteristics |
|------|----------|-----------------|
| **Pure Functions** | `sql_utils.py` | Take `engine` as first param, no class dependency |
| **Bound Methods** | `one/one_*.py` | Use `self.config`, `self.engine`, etc. |

**Write operations:** none ship by default. They are inherently dataset
specific, so a dataset that needs them adds `@tool` methods in `one_04_agent.py`
and registers them in the agent's `tools=[]` list. Keep the underlying helpers
pure — `engine` as the first parameter, returning a dict — the way `sql_utils.py`
does.

**Pure Functions (sql_utils.py):**
- `format_result(result)` - Format SQL result as Markdown table
- `ensure_valid_select_query(query)` - Validate SELECT statement
- `execute_and_print_result(engine, sql)` - Execute query and return Markdown

### Key Singletons

```python
from agent_app.api import one           # Main app instance
from agent_app.paths import path_enum   # All paths
from agent_app.runtime import runtime   # Runtime detection
from agent_app.project_config import project_config  # config/dataset.toml
```

### Agent Framework

- **Library**: `strands` (Strands Agents SDK)
- **Model**: AWS Bedrock (configurable via `config.model_id`)
- **Tools**: Defined with `@tool` decorator in `one_04_agent.py`
- **System Prompt**: `agent_app/prompts/bi-agent-system-prompt.md`

---

## Development Setup

**Package Managers:**
- Python: uv (via mise)
- Node.js: pnpm (via mise)

**Core Configuration Files:**
- `config/site.ts` - All frontend copy and identity (swapped per dataset)
- `config/dataset.toml` - The 4 values Python reads (swapped per dataset)
- `mise.toml` - Project tasks and tool versions (Python 3.12, Node 24, uv, pnpm)
- `pyproject.toml` - Python dependencies and project metadata
- `package.json` - Node.js dependencies
- `.venv/` - Python virtual environment directory
- `node_modules/` - Node.js dependencies directory

**Environment Variables (.env):**

> ⚠️ **Never read, print, or otherwise open `.env`.** It holds real credentials —
> API keys, database passwords, AWS tokens. Read `.env.example` instead: it is the
> committed, placeholder-only template and documents every supported variable.
> If you need to know whether a variable is *set*, check for the key name via
> `.env.example`, or ask the user — do not `cat` / `Read` the `.env` file.

See `.env.example` for the fully documented template. The key switch is `LLM_PROVIDER`:
exactly one LLM backend is active per process, and only *that* provider's credential
is required.

```bash
# bedrock (default) | anthropic | openai | google
LLM_PROVIDER=bedrock
AWS_REGION=us-east-1

# Optional: override the provider's default model (formats are NOT interchangeable)
# LLM_MODEL_ID=us.amazon.nova-lite-v1:0

# Only the key matching LLM_PROVIDER is needed
# ANTHROPIC_API_KEY=sk-ant-...   (requires: uv sync --extra anthropic)
# OPENAI_API_KEY=sk-...          (requires: uv sync --extra openai)
# GOOGLE_API_KEY=...             (requires: uv sync --extra gemini)

# Unused locally (local runtime reads tmp/data.sqlite); needed for remote Postgres
# DB_HOST=ep-xxx-pooler.us-east-1.aws.neon.tech
# DB_PORT=5432
# DB_USER=neondb_owner
# DB_PASS=your_password
# DB_NAME=neondb
```

For `LLM_PROVIDER=bedrock` locally, do **not** set `AWS_ACCESS_KEY_ID` /
`AWS_SECRET_ACCESS_KEY` in `.env` — boto3 reads env vars before `~/.aws/credentials`,
so a placeholder there shadows a working local profile.

---

## Tests

**Python Tests:**
- Location: `tests_python/`
- Runner: pytest
- Command: `mise run test-python`

**Test File Mapping:**
```
tests_python/
├── config/
│   └── test_config_conf_00_def.py  # Tests for Config class
├── one/
│   ├── test_one_one_00_main.py     # Tests for One class
│   ├── test_one_one_01_config.py   # Tests for ConfigMixin
│   └── test_one_one_02_db.py       # Tests for DbMixin
├── test_api.py                     # Tests for api.py
└── test_utils.py                   # Tests for utilities
```

**Node.js Tests:**
- Location: `tests_node/`
- Runner: Node's built-in test module
- Command: `mise run test-node`

---

## Available Tasks

- `mise run venv-create` - Create Python virtual environment
- `mise run venv-remove` - Remove virtual environment
- `mise run inst-python-deps` - Install Python dependencies
- `mise run inst-node-deps` - Install Node.js dependencies
- `mise run inst` - Install all dependencies (Python + Node.js)
- `mise run setup-db` - Seed `tmp/data.sqlite` from the committed `data.sqlite.example`
- `mise run test-python` - Run Python tests
- `mise run test-node` - Run Node.js tests
- `mise run test` - Run all tests (Python + Node.js)
- `mise run export` - Export Python requirements to requirements.txt
- `mise run dev` - Start all development servers (Next.js + FastAPI, auto-kills old instances first)
- `mise run kill` - Kill all running development servers
- `mise run check` - Verify the repo agrees with its config (run after a dataset swap)

---

## Database

**Two databases, two naming schemes:**

| | Local | Remote |
|---|---|---|
| Engine | SQLite `tmp/data.sqlite` | PostgreSQL (NeonDB) |
| Table names | `loan`, `customer`, … | `smbll_loan`, `smbll_customer`, … |
| Used by | local dev + tests | Vercel deployment |

The remote instance is **shared with other projects**, so every table this project
owns is prefixed with `config.project_name_snake` (from `project.name` in
`config/dataset.toml`). Foreign
keys are rewritten to match, and the sync script only ever touches prefixed
tables — other projects' tables are never dropped. `database_schema_str` likewise
reflects only prefixed tables when running remotely, so the agent never sees
another project's schema.

Dependency order lives in `config/dataset.toml` under
`database.tableInsertOrder`, exposed to Python as `TABLE_INSERT_ORDER` in
`agent_app/tests/db_sync.py`: inserts walk it forwards, drops walk it backwards.
Add a new table there, in the right position, or the sync breaks —
`mise run check` compares the list against the SQLite file and fails on a
mismatch in either direction.

**Schema Reference:**
- Run `.venv/bin/python scripts/test_04_print_database_schema.py` to print the schema.
  There is deliberately no checked-in copy: a snapshot of a generated artifact can
  only ever be right by coincidence, and this one had no reader.

**Run SQL Locally:**
```bash
.venv/bin/python scripts/test_03_run_sql_locally_cli.py --sql "SELECT * FROM table_name LIMIT 5"
```

**Print LLM-Optimized Schema:**
```bash
.venv/bin/python scripts/test_04_print_database_schema.py
```

---

## Scripts

Scripts in `scripts/` are numbered in the order you would run them when setting a
project up from scratch. The number is the workflow position, not a priority — run
them in sequence the first time, then individually as needed.

| # | Script | What it does |
|---|--------|--------------|
| 00 | `test_00_check_project_config.py` | Verify the repo agrees with its config (also `mise run check`) |
| 01 | `test_01_setup_sqlite_file.py` | Seed `tmp/data.sqlite` from `data.sqlite.example` (also `mise run setup-db`) |
| 02 | `test_02_run_sql_locally.py` | Run the SQL in `test_02_run_sql_locally.sql` against local SQLite |
| 03 | `test_03_run_sql_locally_cli.py` | Same, but takes `--sql "..."` on the command line |
| 04 | `test_04_print_database_schema.py` | Print the LLM-optimized schema string |
| 05 | `test_05_connect_remote_database.py` | Smoke-test the NeonDB Postgres connection (`SELECT 1`) |
| 06 | `test_06_sync_data_to_remote_db.py` | Drop, recreate, and repopulate the remote DB from local SQLite |
| 07 | `test_07_verify_remote_data.py` | Confirm the remote DB really matches local, table by table (exit 1 on mismatch) |
| 11 | `test_11_ai_aws_bedrock.py` | Raw Bedrock `converse` call — proves AWS credentials work |
| 12 | `test_12_ai_aws_bedrock_with_cached_prompt.py` | Bedrock prompt caching demo (not a connectivity check) |
| 13 | `test_13_ai_anthropic_claude.py` | Raw Anthropic `messages.create` — proves `ANTHROPIC_API_KEY` works |
| 14 | `test_14_ai_openai.py` | Raw OpenAI `chat.completions.create` — proves `OPENAI_API_KEY` works |
| 15 | `test_15_ai_google_gemini.py` | Raw Gemini `generate_content` — proves `GOOGLE_API_KEY` works |

Steps 01-04 are local only. Steps 05-07 need the `DB_*` variables set (see `.env.example`).

Scripts 11-15 hit each supported LLM provider through that vendor's **lowest-level
SDK call** — no `strands`, no agent, no project config. They exist so a student can
see the raw API shape and confirm a key or IAM permission is actually valid before
debugging anything higher up. 11 and 12 are the two Bedrock scripts (basic call, then
prompt caching); 13-15 are one per API-key provider and each needs its extra installed
(`uv sync --extra anthropic|openai|gemini`). Bedrock needs no extra, since boto3 is a
core dependency.

**When adding a script:** give it the next number for its stage, or insert it at the
right position and renumber the ones after it — keep the sequence meaningful rather
than append-only. Unnumbered scripts (`test_agent.py`, `test_ai_*.py`, …) are
standalone experiments outside this setup workflow.
