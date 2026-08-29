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
data/                        # EVERY AUTHORED ARTIFACT a dataset swap rewrites.
│                            #   Content only -- the one config value a swap
│                            #   changes (SCHEMA_NAME) is in .env.defaults.
├── site.toml                #   Every sentence the frontend says, incl. the 12
│                            #   kickstart questions and the 4 capability cards.
├── business-context.md      #   The long-form explainer behind the home page.
└── system-prompt.md         #   The agent's domain brain.

dataset/                     # The dataset's own source material. Committed --
├── 0*-*.md                  #   summary, business context, ER doc, SQL queries
├── 04-*_data_generator*.py  #   ...but its OUTPUT is not: run the generator to
├── requirements.txt         #   build <name>.sqlite and data/*.tsv locally.
└── <name>.sqlite            #   gitignored; discovered by paths.py, not named.

agent_app/                   # Python package. Name is deliberately generic and
├── api.py                   #   never changes when the dataset changes.
├── paths.py
├── runtime.py
├── constants.py
├── sql_utils.py
├── ai_sdk_adapter.py
│
├── config.py                # Reads .env + .env.defaults. Nothing else parses
│                            #   configuration; data/ holds content only.
├── dataset.py               # TEACHING LAYER, meant to be deleted. Discovers
│                            #   dataset/*.sqlite and its generator, runs the
│                            #   generator, syncs to PostgreSQL. Nothing on the
│                            #   production path imports it.
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

Two files feed `agent_app/config.py`. **The line between them is whether the value
is a secret**, because that is what decides who — and which AI — may open the
file:

| | `.env.defaults` | `.env` |
|---|---|---|
| Holds | `SCHEMA_NAME`, LLM provider/model, region, DB port, the whole quota block | API keys, AWS keys, DB host/user/password/name |
| Secret | No | **Yes** |
| In Git | **Yes** | No |
| AI may read | Yes | **No** — `deny` in `.claude/settings.json` |
| AI may edit | Yes — this is what a dataset swap changes | **No** |
| Precedence | Loaded second; fills in the gaps | Loaded **first**; wins |

Rotating an API key must not touch the schema name; pointing the repo at a new
dataset must not touch anyone's credentials.

There is deliberately **no `.env.defaults.example`**. The file is committed, so
it *is* the reference. A gitignored-plus-template arrangement would put
`SCHEMA_NAME` outside version control, make every clone re-enter it, and hide an
AI's swap edits from review — which is the opposite of the point.

`data/` is the third leg and holds no config at all: only authored content
(copy, prompt, explainer, seed).

**The test for which file a value belongs in: is it a secret?** Not "does it
vary by environment" — that used to be the question, when the split was
`data/dataset.toml` vs `.env`, and it produced a whole TOML file plus a reader
module for what ended up being one string. The split that earns its keep is the
one that decides *who may touch the file*:

- `.env` holds credentials. It is gitignored, and `.claude/settings.json` denies
  an AI both `Read` and `Edit` on it.
- `.env.defaults` holds everything that is not a credential, including the
  dataset's `SCHEMA_NAME`. It is committed, so a change shows up in `git diff`
  like any other, and an AI doing a dataset swap may edit it freely.

`.env` is loaded first and wins, so any committed default can be overridden on
one machine by repeating the key in `.env` — that is how a checkout points at a
staging schema without editing a committed file.

A value still must not have two homes *within* a layer. `project_name` was once
duplicated between `Config` and the dataset config and is gone entirely;
`schemaName` and `project.name` were two names for one thing and are now one.

**`data/` is content, not config.** Everything in it is authored prose, copy, or
data: the frontend's strings, the explainer, the system prompt, the SQLite seed.
Nothing in `agent_app/` parses a config file out of it. Before adding something
there, ask whether a human wrote it as content; if it is a setting, it goes in
`.env.defaults`.

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
the literal trigger phrase that makes the block appear. `mise run check-content` fails
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
| The PostgreSQL schema name | `SCHEMA_NAME` in `.env.defaults` |
| Agent's domain knowledge | `data/system-prompt.md` |
| The data itself | `dataset/` — source docs plus the generator that builds `<name>.sqlite` |
| Dataset-specific write tools | `@tool` methods in `one_04_agent.py` |

The only entry not in `data/` is the last one, because a write tool is code.

Run `mise run check-content` afterwards. It fails on a seed whose foreign keys form a
cycle (or that has no tables at all), a prompt that queries a nonexistent table,
missing content files, and a kickstart question whose `render` disagrees with
its own wording. Right after a swap also run it with the outgoing domain's
vocabulary, which is a one-off argument rather than committed state:

```bash
mise run check-content -- --retired "patient,bed,ward,nurse"
```

Icon names are checked by `mise run build-web`, not by `mise run check-content`:
`lib/site/load.ts` rejects any `icon` that `lib/icons.ts` does not export. Run
the build too, since the check script never parses the TOML's icon fields.

### When to Modify Each File

**Root Level Modules:**

| File | What It Does | When to Modify |
|------|--------------|----------------|
| `api.py` | Re-exports `one` singleton | Rarely. Only if you need to expose additional top-level imports. |
| `paths.py` | Defines all file/directory paths as `PathEnum`, including the system prompt | When adding new files (prompts, data files, output paths). Add path here first, then use `path_enum.your_new_path` everywhere. Paths are source-tree facts, so they are never named in config. Never add one speculatively: an entry with no reader rots into a pointer at a directory that no longer exists. |
| `runtime.py` | Detects runtime environment (local vs vercel) | When adding a new deployment target (e.g., AWS Lambda). Add new enum value and detection logic. |
| `constants.py` | Shared enums: the LLM provider list, and the schema-encoding vocabulary | When adding an enum a *second* module needs. A constant with one reader belongs next to that reader, not here. |
| `utils.py` | Helpers with no project dependencies: `debug` (stderr, never stdout) and `match` (include/exclude patterns) | Same rule as `constants.py` — only what a *second* module needs. |
| `sql_utils.py` | Pure functions for SQL execution and formatting. Owns one promise: a query run through `execute_sql_query` cannot change the database | When changing how SQL results are formatted or adding new query validation rules. Every failure is *returned as text*, never raised — the caller is an LLM, and a traceback ends its turn. |
| `ai_sdk_adapter.py` | Converts Vercel AI SDK messages <-> Strands Agent messages, and generates the SSE event stream back to the browser | When the frontend message format changes. **Not** when switching LLM provider — this file is provider-agnostic and must stay that way; provider code belongs in `one_04_agent.py`. |
| `vendor/vercel_ai_sdk.py` | Pydantic data model for the AI SDK request body. Vendored from `vercel-ai-sdk-mate`, deliberately lenient so a new AI SDK release cannot break request parsing | When the frontend starts sending a message part type the backend needs to read: add the model class and one line to `PART_MODEL_BY_TYPE`. Keep it a pure data model — no provider logic. |

**config/ Directory:**

| File | What It Does | When to Modify |
|------|--------------|----------------|
| `config.py` | The `Config` dataclass, and `load_env_files()` which reads `.env` then `.env.defaults` | When adding an environment variable: add a field, load it in **both** `new_in_local_runtime()` and `new_in_vercel_runtime()`, and document it in `.env.defaults` (not a secret) or `.env.example` (secret). There is no module-level `config` singleton — callers use `one.config`. |

**one/ Directory (Main Class + Mixins):**

| File | What It Does | When to Modify |
|------|--------------|----------------|
| `one_00_main.py` | Defines `One` class that inherits all mixins; creates `one` singleton | When adding a new mixin (import it and add to inheritance list). |
| `one_01_config.py` | `ConfigMixin`: provides `self.config` | Rarely. Config loading logic is in `config.py`. |
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

**db_schema/ Directory:**

Three steps in one direction — reflect, model, encode — and nothing flows back.

| File | What It Does | When to Modify |
|------|--------------|----------------|
| `extractor.py` | SQLAlchemy metadata -> the models. Owns `SQLALCHEMY_TYPE_MAPPING`, the compression from SQL types to the LLM vocabulary | When a reflected type comes out as a raw dialect spelling instead of a compact one. |
| `model.py` | The intermediate representation | **Only together with the encoder line that emits the new field.** Every field here has a reader; extracting one nobody encodes reads as a promise the output does not keep. |
| `encoder.py` | The models -> the compact string the agent is shown. Pure formatting, no database access | When changing how the schema is presented to the LLM. Re-run `scripts/test_04_print_database_schema.py` and eyeball the diff — this string is the agent's entire picture of the database. |
| `api.py` | Public re-exports | When adding a function the rest of the app calls. |

Scoped to what this app runs on. `DbTypeEnum` lists the two engines with code
paths (SQLite seed, PostgreSQL serving) rather than the ten it once advertised —
a menu of unimplemented options reads as support that does not exist. The type
mapping is the deliberate exception: a missing key degrades to the dialect's own
spelling rather than failing, so breadth there costs nothing.

### Class Hierarchy

```
One (one_00_main.py)
├── ConfigMixin (one_01_config.py)
│   └── self.config -> Config instance (from config.py)
│
├── DbMixin (one_02_db.py)
│   ├── self.remote_postgres_engine -> PostgreSQL (NeonDB)
│   ├── self.engine                -> Auto-selects based on runtime
│   ├── self.database_schema_str   -> LLM-optimized schema string
│   └── self.execute_sql_query(sql)        -> Markdown table
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
- `execute_sql_query(engine, sql)` - Execute a read-only query, return Markdown
- `new_sqlite_engine(path)` - Open SQLite so that the rollback guarantee holds

### Key Singletons

```python
from agent_app.api import one           # Main app instance
from agent_app.paths import path_enum   # All paths
from agent_app.runtime import runtime   # Runtime detection

one.config.schema_name                 # SCHEMA_NAME, from .env.defaults
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
- `.env.defaults` - Committed, non-secret config incl. `SCHEMA_NAME`. AI-editable
- `.env` - Secrets. Gitignored, and denied to AI in `.claude/settings.json`
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

# Required everywhere: the agent reads PostgreSQL in every environment
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
├── test_config.py                  # Tests for config.py
├── db_schema/
│   ├── test_db_schema_encoder.py   # Tests for encoder.py
│   └── test_db_schema_extractor.py # Tests for extractor.py
├── one/
│   ├── test_one_one_00_main.py     # Tests for One class
│   ├── test_one_one_01_config.py   # Tests for ConfigMixin
│   └── test_one_one_02_db.py       # Tests for DbMixin
├── test_api.py                     # Tests for api.py
├── test_source_code.py             # Tests for source_code.py (the TDD lesson)
└── test_utils.py                   # Tests for utilities
```

**No test opens a network connection.** The `db_schema` tests build
`sa.MetaData` by hand and reflect through in-memory SQLite, which is enough
because the extractor only ever touches SQLAlchemy objects. What genuinely needs
PostgreSQL — `search_path` pinning, the remote sync — is exercised by the
numbered scripts in `scripts/`, not by pytest.

**Use a fictional domain in test fixtures** (`acme`, `widget`, `part`), never
this dataset's real table names. A test asserting on `loan` silently becomes a
lie the next time the dataset is swapped.

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
- `mise run test-python` - Run Python tests
- `mise run test-node` - Run Node.js tests
- `mise run test` - Run all tests (content consistency + Python + Node.js)
- `mise run cov` - Run tests with a coverage report, written to `htmlcov/`
- `mise run export` - Export Python requirements to requirements.txt
- `mise run dev` - Start all development servers (Next.js + FastAPI, auto-kills this project's old instances first)
- `mise run kill` - Kill this project's development servers
- `mise run check-content` - Verify `data/` still agrees with the prompt and the seed (run after a dataset swap)
- `mise run build-web` - Build the Next.js frontend; the only check for `site.toml` keys and icon names

`check-content` and `build-web` are the two halves of "did the swap land", and
neither catches what the other does. Run both.

### The app's own CLI

```bash
.venv/bin/agent-app check-content
.venv/bin/agent-app check-content --retired "patient,bed,ward"
```

Installed as a console script by `[project.scripts]` in `pyproject.toml`, backed
by `agent_app/cli.py`. **`mise.toml` calls this name rather than a file path**, so
where a command's implementation lives can change without every task and habit
changing with it.

**Only application commands belong here.** Building the dataset and publishing it
to PostgreSQL stay in the teaching layer's own CLI (`teaching_cli.py`): that layer
is deleted as whole directories, and a shared entry point would leave a broken
subcommand behind. The test for a new command is the repo's usual one — is it part
of this app, or part of teaching someone to build it?

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

| | Local seed | What the agent reads |
|---|---|---|
| Engine | SQLite `dataset/<name>.sqlite` | PostgreSQL (NeonDB) |
| Table names | `loan`, `customer`, … | `loan`, `customer`, … — **identical** |
| Used by | the sync's source, and tests | every environment, laptop included |

**The database is not in Git.** `dataset/` holds the source documents and the
generator; running the generator produces `dataset/<name>.sqlite`, which
`.gitignore` excludes along with `dataset/data/*.tsv`. A fresh checkout therefore
has to build it:

```bash
.venv/bin/python .claude/skills/about-bi-agent-app-scaffold-cn/scripts/teaching_cli.py gen-data
.venv/bin/python .claude/skills/about-bi-agent-app-scaffold-cn/scripts/teaching_cli.py sync-db
```

Those are **not** mise tasks on purpose: `mise.toml` runs the application, and
none of this is the application. The teaching layer is a set of directories you
delete, not lines to pick out of a shared config.

`agent_app/paths.py` **discovers** that file rather than naming it — the
filename belongs to the dataset, and naming it would make a swap edit
`agent_app/`, which is the one thing that package is not supposed to need. Zero
matches and several matches both raise, with the fix in the message.

The remote instance is **shared with other projects**, and the isolation is a
PostgreSQL **schema**, not a table-name prefix: `SCHEMA_NAME` in
`.env.defaults`. Table names are the same on both sides, and that is the
whole point — an earlier revision prefixed every table (`smbll_loan`), which
made the name the agent saw depend on which engine was behind it, so every SQL
example in the system prompt was right in one environment and wrong in the
other, with nothing failing loudly.

Foreign keys are rewritten into the schema, and the sync only ever touches its
own schema — other projects' tables are never dropped. `database_schema_str`
reflects only that schema, so the agent never sees another project's tables.

Dependency order is **computed, not configured**: `table_insert_order()` in
`agent_app/tests/db_sync.py` is a thin name over SQLAlchemy's
`metadata.sorted_tables`, itself a topological sort of the reflected foreign
keys. Inserts walk it forwards, drops walk it backwards. **Adding a table needs
no config change** — reflect it and the order updates itself.

There used to be a hand-written `tableInsertOrder` list plus a check comparing
it against the seed. Both are gone: a hand-copied topological sort is a value
that can be wrong, and the only thing that check could catch was someone copying
it wrong. `mise run check-content` now verifies the thing derivation *cannot* fix — that
the foreign keys admit an order at all, i.e. contain no cycle.

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
| 00 | `test_00_check_project_config.py` | Numbered door onto `agent-app check-content`. The checks live in `agent_app/content_check.py`; this file only forwards to them |
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
