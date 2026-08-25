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
data/                        # EVERYTHING a dataset swap rewrites, and nothing else.
├── dataset.toml             #   The handful of values Python reads.
├── site.toml                #   Every sentence the frontend says, incl. the 12
│                            #   kickstart questions and the 4 capability cards.
├── business-context.md      #   The long-form explainer behind the home page.
├── system-prompt.md         #   The agent's domain brain.
└── data.sqlite.example      #   Pristine seed, copied to tmp/data.sqlite.

agent_app/                   # Python package. Name is deliberately generic and
├── api.py                   #   never changes when the dataset changes.
├── paths.py
├── project_config.py        # Typed reader over data/dataset.toml
├── runtime.py
├── constants.py
├── sql_utils.py
├── ai_sdk_adapter.py
│
├── config/                  # NOTE: secrets from .env -- NOT data/*.toml
│   └── conf_00_def.py
│
├── vendor/                  # Third-party code copied in, not installed.
│   └── vercel_ai_sdk.py     #   AI SDK request-body data model. No project
│                            #   logic goes in here.
│
├── one/
│   ├── one_00_main.py
│   ├── one_01_config.py
│   ├── one_02_db.py
│   ├── one_03_boto3.py
│   ├── one_04_agent.py
│   └── api.py
│
└── db_schema/

lib/
├── icons.ts                 # Icon-name -> component map; exports the IconName type
├── constants.ts             # Derived view of data/site.toml; authored nothing
└── site/
    ├── schema.ts            # The shape data/site.toml must have, plus the
    │                        #   required-key list checked at load
    └── load.ts              # Parses the TOML once. SERVER ONLY (reads disk).

components/
├── CapabilityCard.tsx       # One business thread. Home page AND agent page
│                            #   render this, from one [[capabilities]] entry.
├── BusinessContextModal.tsx # Renders business-context.md as Markdown
├── ConceptTooltip.tsx       # The hover/focus/tap bubble behind a concept name
└── chat/
    └── RenderBadge.tsx      # The glyph promising what a kickstart draws
```

### The Two Kinds of "Config"

Two things in this repo are called config. They change for different reasons and
must not be mixed:

| | `data/` | `.env` → `agent_app/config/` |
|---|---|---|
| Holds | Project identity, business copy, table order | API keys, DB credentials, LLM provider |
| Differs per | **dataset** | **machine** |
| In Git | Yes | No |
| Read by | Next.js *and* Python | Python only |

Rotating an API key must not touch the project's name; pointing the repo at a
new dataset must not touch anyone's credentials.

**The test for which layer a value belongs to: does it vary by environment?**
`agent_app/project_config.py` reads `data/dataset.toml` and nothing in it
varies by environment. Local, Vercel, and CI all serve the same dataset, so they
all get the same answer. `agent_app/config/conf_00_def.py` holds everything that
*does* differ per machine. A value must not appear in both, not even with an
environment variable as an "escape hatch": that gives it two homes and
eventually two answers. `project_name` used to be duplicated that way and is
now only in `project_config`.

**`data/` is split by consumer, not by topic.** The frontend and the backend
read disjoint sets of keys, so one shared file was two unrelated files stapled
together. `site.toml` is read only by Next.js, `dataset.toml` only by Python.
Before adding a value, ask which runtime consumes it; if the answer is "both",
say so out loud, because today nothing does.

**Why the site copy is TOML rather than TypeScript.** It used to be
`config/site.ts`, and the argument for that was real: the compiler checked the
shape for free and a misspelled icon name was a build error. What outweighed it
is that the copy belongs to the *dataset*, not to the frontend. Keeping it in
`lib/`-adjacent TypeScript meant a dataset swap was a diff scattered across the
repo; keeping every authored artifact in `data/` makes a swap a directory
replacement, which is a far easier thing to get right and to review.

The checks the compiler used to perform are not gone, they moved into
`lib/site/load.ts` and run when Next.js reads the file: `REQUIRED_SITE_KEYS`
rejects a missing key by name, and `assertIconsExist` rejects an icon that is
not in `lib/icons.ts`. Both throw during `next build`, so a broken `site.toml`
still cannot ship. What genuinely got weaker is editor autocomplete while
authoring the TOML. That was judged an acceptable trade, because authoring
happens once per dataset while reviewing a swap happens every time.

**Both directions of the kickstart contract are machine-checked.** Each of the
12 questions in `site.toml` carries a `render` field, and its `action` carries
the literal trigger phrase that makes the block appear. `mise run check` fails
if the two disagree, in either direction: a wrong phrase means the block never
appears, and a wrong `render` means the button draws an icon promising a chart
over an answer that is prose.

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

Everything that varies between datasets lives in `data/`. When adding UI copy, a
brand string, or a business term, put it in `data/site.toml` — never inline it
in a component.

| What | Where |
|---|---|
| Product name, all UI copy, SEO, icons | `data/site.toml` |
| The 4 capability cards (home page *and* agent page) | `[[capabilities]]` in `data/site.toml` |
| The 12 kickstart questions, with their render quota | `[[chat.suggestedActions]]` in `data/site.toml` |
| The long-form "what problem does this solve" explainer | `data/business-context.md` |
| Table prefix, DB display name, table order | `data/dataset.toml` |
| Agent's domain knowledge | `data/system-prompt.md` |
| The data itself | `data/data.sqlite.example` |
| Dataset-specific write tools | `@tool` methods in `one_04_agent.py` |

The only entry not in `data/` is the last one, because a write tool is code.

Run `mise run check` afterwards. It fails on a `tableInsertOrder` that
disagrees with the SQLite file, a prompt that queries a nonexistent table,
missing content files, and a kickstart question whose `render` disagrees with
its own wording. Right after a swap also run it with the outgoing domain's
vocabulary, which is a one-off argument rather than committed state:

```bash
mise run check -- --retired "patient,bed,ward,nurse"
```

Icon names are checked by `npx next build`, not by `mise run check`:
`lib/site/load.ts` rejects any `icon` that `lib/icons.ts` does not export. Run
the build too, since the check script never parses the TOML's icon fields.

### When to Modify Each File

**Root Level Modules:**

| File | What It Does | When to Modify |
|------|--------------|----------------|
| `api.py` | Re-exports `one` singleton | Rarely. Only if you need to expose additional top-level imports. |
| `paths.py` | Defines all file/directory paths as `PathEnum`, including the system prompt | When adding new files (prompts, data files, output paths). Add path here first, then use `path_enum.your_new_path` everywhere. Paths are source-tree facts, so they are never named in config. |
| `runtime.py` | Detects runtime environment (local vs vercel) | When adding a new deployment target (e.g., AWS Lambda). Add new enum value and detection logic. |
| `constants.py` | Enums and constants | When adding new enum types or magic values that need to be shared across modules. |
| `project_config.py` | Typed reader over `data/dataset.toml`; also owns the `project_name` derivations (`_snake`, `_slug`, `prefix_table_name`) | When Python needs a new dataset value. If it varies by environment it belongs in `config/conf_00_def.py`; if only the frontend reads it, `data/site.toml`. |
| `sql_utils.py` | Pure functions for SQL execution and formatting | When changing how SQL results are formatted or adding new query validation rules. |
| `ai_sdk_adapter.py` | Converts Vercel AI SDK messages <-> Strands Agent messages, and generates the SSE event stream back to the browser | When the frontend message format changes. **Not** when switching LLM provider — this file is provider-agnostic and must stay that way; provider code belongs in `one_04_agent.py`. |
| `vendor/vercel_ai_sdk.py` | Pydantic data model for the AI SDK request body. Vendored from `vercel-ai-sdk-mate`, deliberately lenient so a new AI SDK release cannot break request parsing | When the frontend starts sending a message part type the backend needs to read: add the model class and one line to `PART_MODEL_BY_TYPE`. Keep it a pure data model — no provider logic. |

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

**data/ Directory (everything a dataset swap rewrites):**

| File | What It Does | When to Modify |
|------|--------------|----------------|
| `system-prompt.md` | System prompt for the BI agent | When changing agent behavior, adding tool usage instructions, or updating workflow guidelines. The five rendering sections are copied verbatim from `.claude/skills/swap-dataset-cn/ref/system-prompt-render-blocks.md`; change them in both places or neither. |
| `site.toml` | Every sentence the UI says, the 4 capability cards, the 12 kickstart questions | When changing any user-visible string. Never inline copy in a component. |
| `business-context.md` | The long-form explainer behind the home page | When the domain explanation changes. At most one mermaid diagram in the file. |
| `dataset.toml` | Table prefix, DB display name, table insert order | When adding a table, or pointing at a new dataset. |

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
from agent_app.project_config import project_config  # data/dataset.toml
```

### Agent Framework

- **Library**: `strands` (Strands Agents SDK)
- **Model**: AWS Bedrock (configurable via `config.model_id`)
- **Tools**: Defined with `@tool` decorator in `one_04_agent.py`
- **System Prompt**: `data/system-prompt.md`

---

## Development Setup

**Package Managers:**
- Python: uv (via mise)
- Node.js: pnpm (via mise)

**Core Configuration Files:**
- `data/site.toml` - All frontend copy and identity (swapped per dataset)
- `data/dataset.toml` - The values Python reads (swapped per dataset)
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
- `mise run setup-db` - Seed `tmp/data.sqlite` from the committed `data/data.sqlite.example`
- `mise run test-python` - Run Python tests
- `mise run test-node` - Run Node.js tests
- `mise run test` - Run all tests (Python + Node.js)
- `mise run export` - Export Python requirements to requirements.txt
- `mise run dev` - Start all development servers (Next.js + FastAPI, auto-kills this project's old instances first)
- `mise run kill` - Kill this project's development servers
- `mise run check` - Verify the repo agrees with its config (run after a dataset swap)

### Running the dev server from an agent session

`mise run dev` never exits on its own. Three rules follow from that, and the
cost of breaking them is a session that looks hung for half an hour.

**1. Never wait on it in the foreground.** Start it with `run_in_background`, or
detached with `nohup`. A foreground call blocks until the server dies, which is
whenever the user happens to stop it.

**2. Wait for readiness in a separate background command that exits by itself.**
One notification, arriving in seconds:

```bash
until grep -q "Ready in" <task-output-file>; do sleep 0.5; done
```

Both halves have to be up, and they log different lines: Next.js prints
`Ready in`, uvicorn prints `Application startup complete.`. Do not poll with a
bare `for` loop and no `sleep` -- that spins the CPU and returns instantly
whether or not the thing ever became ready.

**3. Decide who owns the server before you start it.**

| Why you are starting it | How | Cleanup |
| :--- | :--- | :--- |
| To verify something yourself | `run_in_background` | `TaskStop` as soon as you are done |
| The user asked for a server to use | `nohup ... &`, detached | Leave it; tell the user how to stop it |

A backgrounded task that is still holding a server when the user replaces it
emits a stale failure notification much later -- `mise run dev` exits 143 when
its `kill` dependency terminates the previous instance, which reads as
`task failed` even though nothing went wrong. Detaching a server the user owns
avoids that entirely.

**Interpreting an exit code from `mise run dev`:**

| Code | What happened |
| :--- | :--- |
| 143 | SIGTERM. Normally a second `mise run dev` in this same checkout replaced it. Not an error |
| 1 from the `kill` step, no server started | A dev port is held by a process from another checkout. Intended: stop that one, or `--force`. See `kill-dev-servers.py` |

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
`data/dataset.toml`). Foreign
keys are rewritten to match, and the sync script only ever touches prefixed
tables — other projects' tables are never dropped. `database_schema_str` likewise
reflects only prefixed tables when running remotely, so the agent never sees
another project's schema.

Dependency order lives in `data/dataset.toml` under
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
| 01 | `test_01_setup_sqlite_file.py` | Seed `tmp/data.sqlite` from `data/data.sqlite.example` (also `mise run setup-db`) |
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
