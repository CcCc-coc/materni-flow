# -*- coding: utf-8 -*-

"""
Preflight check: is this repo internally consistent with its own config?

Why this script exists
----------------------

This repo is a template. The same scaffolding — one prompt, one database, one
website — gets pointed at a new dataset and a new business domain over and over.
Everything a swap rewrites now lives in ``data/``: ``dataset.toml`` for what
Python reads, ``site.toml`` for every sentence the UI says, plus the explainer,
the system prompt, and the database seed. Config and content sit side by side
there, but they fail differently -- a missing config key is caught by the
frontend loader, while the prompt and the questions are prose that has to be
rewritten by hand, and prose cannot be type-checked.

Hand-rewriting is where things get forgotten. The evidence is in this repo's own
history: a previous swap updated the prompt and the frontend but left an entire
module of hospital write-operations, and three docstrings describing an
"obstetrics ward scheduling database", sitting in a lending codebase. Nothing
failed. Nothing complained. The code simply lied for months.

So this script's job is to make that class of mistake **loud**. Every check here
compares two things that a swap must keep in agreement, and fails the build when
they disagree.

What it checks
--------------

1. **Table order vs. reality** — ``database.tableInsertOrder`` must match the
   tables actually present in the SQLite file, in both directions.
2. **Prompt vs. schema** — every table the system prompt writes ``FROM`` or
   ``JOIN`` against must exist in the database.
3. **Content files** — the system prompt, the site copy, and the explainer must
   exist and be non-trivial.
4. **Render quota** — the twelve kickstart questions must be three of each kind,
   and each question's ``render`` must agree with the trigger phrase inside its
   ``action``. Both directions, because they fail differently: a wrong phrase
   means the block never appears, and a wrong ``render`` means the button draws
   an icon promising something the answer will not contain.
5. **Retired vocabulary** — opt in with ``--retired``, for the one run right
   after a dataset swap.

Icon names are not checked here. ``lib/site/load.ts`` checks them against
``lib/icons.ts`` when Next.js reads the TOML, which is a real check at build
time rather than a second list to keep in step.

Usage::

    mise run check
    .venv/bin/python scripts/test_00_check_project_config.py
"""

import argparse
import re
import sys
import tomllib
import typing as T
from pathlib import Path

import sqlalchemy as sa

from agent_app.paths import path_enum
from agent_app.tests.db_sync import table_insert_order


#: Directories worth scanning for retired vocabulary: everything that is code or
#: config. Prose is deliberately excluded — ``docs/`` and ``blogs/`` legitimately
#: discuss past datasets, and failing on a tutorial that explains the previous
#: domain would train the reader to ignore this script.
SCAN_DIRS = [
    "app",
    "components",
    "lib",
    "data",
    "types",
    "api",
    "agent_app",
    "scripts",
    "tests_python",
    "config",
]

#: File extensions worth scanning inside :data:`SCAN_DIRS`.
SCAN_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".sql"}

#: Files exempt from the retired-vocabulary scan, because listing those words is
#: precisely their job.
SCAN_EXEMPT = {
    "scripts/test_00_check_project_config.py",
}

#: Identifiers that can follow FROM/JOIN in the system prompt without naming a
#: real table: SQL keywords, and the generic stand-ins a prompt uses when it is
#: illustrating a shape rather than a query ("... FROM table").
PROMPT_NON_TABLES = {
    "select",
    "lateral",
    "unnest",
    "values",
    "table",
    "table_name",
    "your_table",
}


class Report:
    """
    Accumulates findings so that one run reports *every* problem, not just the
    first.

    A checker that stops at the first failure turns a swap into a slow
    fix-one-rerun loop. Collecting everything means one run gives you the whole
    list of what still needs doing.
    """

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, check: str, message: str):
        self.errors.append(f"[{check}] {message}")

    def warn(self, check: str, message: str):
        self.warnings.append(f"[{check}] {message}")

    def section(self, title: str, ok: bool):
        mark = "PASS" if ok else "FAIL"
        print(f"  {mark}  {title}")


def iter_scan_files() -> T.Iterator[Path]:
    """Yield every code/config file that the retired-vocabulary scan covers."""
    root = path_enum.dir_project_root
    for dir_name in SCAN_DIRS:
        directory = root / dir_name
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in SCAN_SUFFIXES:
                continue
            if "__pycache__" in path.parts or "node_modules" in path.parts:
                continue
            if str(path.relative_to(root)) in SCAN_EXEMPT:
                continue
            yield path


def check_retired_terms(report: Report, terms: list[str]) -> bool:
    """
    Fail if vocabulary from a retired dataset still appears in the code.

    Terms come from ``--retired``, not from a committed config file. That is
    deliberate. This check is a *migration* tool: its value peaks the day you
    swap datasets and drops to zero once the swap is clean. Storing the previous
    domain's nouns in the repo forever meant every later reader found words from
    a dead dataset sitting in the current one's config, and meant the list
    silently rotted whenever someone forgot to update it.

    Run it by hand right after a swap::

        mise run check -- --retired "patient,bed,ward,nurse"

    Matching is whole-word and case-insensitive, so ``bed`` flags a stray
    hospital reference without flagging ``bedrock``.
    """
    if not terms:
        return True

    pattern = re.compile(
        r"\b(" + "|".join(re.escape(t) for t in terms) + r")\b",
        re.IGNORECASE,
    )
    root = path_enum.dir_project_root
    hits = 0
    for path in iter_scan_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            match = pattern.search(line)
            if match:
                hits += 1
                report.error(
                    "retired-terms",
                    f"{path.relative_to(root)}:{lineno} still says "
                    f"{match.group(0)!r} — left over from a previous dataset.",
                )

    ok = hits == 0
    report.section(f"retired vocabulary ({len(terms)} terms)", ok)
    return ok


def sqlite_table_names() -> set[str]:
    """Reflect the local SQLite file and return its table names."""
    engine = sa.create_engine(f"sqlite:///{path_enum.path_sqlite_db}")
    metadata = sa.MetaData()
    metadata.reflect(bind=engine)
    return set(metadata.tables)


def check_table_insert_order(report: Report, db_tables: set[str]) -> bool:
    """
    Fail if the seed's foreign keys admit no insert order at all.

    The order itself is no longer configured -- the sync reads it off
    ``metadata.sorted_tables`` -- so there is no list left to disagree with the
    file. What can still go wrong is a foreign-key *cycle*: two tables that each
    require the other to exist first. SQLAlchemy raises on it, and the honest
    place to hit that is here rather than halfway through writing the remote
    database.

    An empty seed is the other failure: it reflects cleanly and syncs nothing.
    """
    if not db_tables:
        report.error(
            "table-order",
            f"{path_enum.path_sqlite_db.name} has no tables. "
            f"Re-seed it with: mise run setup-db",
        )
        report.section("table insert order (0 tables)", False)
        return False

    metadata = sa.MetaData()
    metadata.reflect(bind=sa.create_engine(f"sqlite:///{path_enum.path_sqlite_db}"))
    try:
        order = table_insert_order(metadata)
    except sa.exc.CircularDependencyError as e:
        report.error(
            "table-order",
            f"the seed's foreign keys form a cycle, so no insert order can "
            f"satisfy them: {e}",
        )
        report.section("table insert order (cycle)", False)
        return False

    report.section(f"table insert order ({len(order)} tables)", True)
    return True


def check_prompt_tables(report: Report, db_tables: set[str]) -> bool:
    """
    Fail if the system prompt queries a table the database does not have.

    Scans for identifiers following ``FROM`` and ``JOIN``, **inside ```sql
    fenced blocks only**. A prompt that teaches the agent to query a table left
    behind by the previous dataset produces confident, entirely wrong SQL at
    runtime.

    Scoping to the fenced blocks is what keeps this honest. Scanning the whole
    file cannot tell prose from SQL, and the prompt legitimately discusses SQL
    in prose: the dialect section says to write ``EXTRACT(QUARTER FROM d)``
    rather than ``strftime``, and a whole-file scan reads that as a query
    against a table called ``d``. The previous version reported three such
    tables and no real ones.

    A dotted name is skipped too. ``EXTRACT(QUARTER FROM l.disbursement_date)``
    is a column reference that happens to follow ``FROM``, and a real one
    appears inside the SQL examples.

    Names the prompt defines itself as CTEs (``WITH early_behavior AS (...)``)
    are resolved and excluded — they read exactly like table references but are
    local to the query, so flagging them would be pure noise.
    """
    path = path_enum.path_bi_agent_system_prompt_md
    if not path.exists():
        report.error("prompt-tables", f"system prompt not found at {path}")
        report.section("prompt table references", False)
        return False

    text = path.read_text(encoding="utf-8")
    sql_blocks = "\n".join(re.findall(r"```sql\n(.*?)```", text, re.S))
    referenced = set(
        name.lower()
        for name in re.findall(
            # The trailing `(?!\.)` drops `FROM l.disbursement_date`, which is a
            # column inside EXTRACT rather than a table.
            r"\b(?:FROM|JOIN)\s+([a-z_][a-z0-9_]*)(?!\s*\.)",
            sql_blocks,
            re.IGNORECASE,
        )
    )

    # CTEs the prompt defines itself: `WITH name AS (` and `, name AS (`.
    cte_names = set(
        name.lower()
        for name in re.findall(
            r"(?:\bWITH\s+|,\s*)([a-z_][a-z0-9_]*)\s+AS\s*\(",
            sql_blocks,
            re.IGNORECASE,
        )
    )

    referenced -= PROMPT_NON_TABLES
    referenced -= cte_names

    unknown = sorted(t for t in referenced if t not in db_tables)
    for name in unknown:
        report.error(
            "prompt-tables",
            f"the system prompt queries table {name!r}, which does not exist in "
            f"the database. The agent will write SQL that always errors.",
        )

    ok = not unknown
    report.section(f"prompt table references ({len(referenced)} found)", ok)
    return ok


def check_content_files(report: Report) -> bool:
    """Fail if the hand-written content a swap must replace is missing or empty."""
    ok = True

    for label, path, floor in (
        ("system prompt", path_enum.path_bi_agent_system_prompt_md, 500),
        ("site copy", path_enum.path_site_toml, 500),
        ("business context", path_enum.path_business_context_md, 500),
    ):
        if not path.exists():
            report.error("content", f"{label} missing: {path}")
            ok = False
        elif len(path.read_text(encoding="utf-8").strip()) < floor:
            report.error("content", f"{label} looks like a stub: {path}")
            ok = False

    report.section("content files", ok)
    return ok



#: How many kickstart questions of each kind `data/site.toml` must carry.
#:
#: Twelve buttons that all return prose leave the diagram renderer and the chart
#: renderer with nothing to draw, which is the same as not having built them.
RENDER_QUOTAS = {"table": 3, "flowchart": 3, "chart": 3, "free": 3}

#: The phrase that actually makes each block appear.
#:
#: The other half of the contract in the prompt's ``## Rendering Triggers``
#: table. The model follows the wording, not the intent, so these are literal.
RENDER_PHRASES = {
    "table": (("as a markdown table",), ("show the sql",)),
    "flowchart": (("as a flowchart", "as a diagram"),),
    "chart": (("as a bar chart", "as a line chart"),),
}


def kind_from_phrases(action: str) -> str:
    """Which block this question's wording will actually produce."""
    hits = [
        kind
        for kind, groups in RENDER_PHRASES.items()
        if all(any(p in action for p in group) for group in groups)
    ]
    if len(hits) == 1:
        return hits[0]
    return "ambiguous" if hits else "free"


def check_render_quota(report: Report) -> bool:
    """Fail if the kickstart questions do not exercise every renderer.

    Checked in both directions on purpose. ``render`` is what the button
    promises the reader, the phrase is what the model reacts to, and each can be
    wrong without the other noticing: a question marked ``chart`` whose wording
    forgot "as a bar chart" draws a chart icon over a paragraph of prose.
    """
    ok = True
    site_toml = path_enum.path_site_toml
    if not site_toml.exists():
        report.section("render quota", False)
        return False

    actions = tomllib.loads(site_toml.read_text(encoding="utf-8")).get("chat", {}).get(
        "suggestedActions", []
    )
    tally: dict[str, int] = {kind: 0 for kind in RENDER_QUOTAS}

    for i, item in enumerate(actions):
        missing = {"render", "title", "label", "action"} - set(item)
        if missing:
            report.error("quota", f"suggestedActions[{i}] is missing {sorted(missing)}")
            ok = False
            continue

        declared = item["render"]
        if declared not in RENDER_QUOTAS:
            report.error(
                "quota",
                f"suggestedActions[{i}] '{item['title']}': unknown render {declared!r}",
            )
            ok = False
            continue

        tally[declared] += 1
        actual = kind_from_phrases(item["action"].lower())
        if actual != declared:
            report.error(
                "quota",
                f"suggestedActions[{i}] '{item['title']}': render is {declared!r} but "
                f"the wording produces {actual!r}",
            )
            ok = False

    for kind, want in RENDER_QUOTAS.items():
        if tally[kind] != want:
            report.error("quota", f"{tally[kind]} {kind} question(s), expected {want}")
            ok = False

    report.section(f"render quota ({len(actions)} questions)", ok)
    return ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--retired",
        default="",
        metavar="WORDS",
        help=(
            "Comma-separated vocabulary from the dataset this repo used to "
            "serve. Pass it right after a swap to prove none of it survives, "
            "e.g. --retired \"patient,bed,ward\". Omitted by default."
        ),
    )
    args = parser.parse_args(argv)
    retired = [t.strip() for t in args.retired.split(",") if t.strip()]

    print()
    print("Project config consistency check")
    print("=" * 60)

    report = Report()
    db_tables = sqlite_table_names()

    check_retired_terms(report, retired)
    check_table_insert_order(report, db_tables)
    check_prompt_tables(report, db_tables)
    check_content_files(report)
    check_render_quota(report)

    print("=" * 60)

    for warning in report.warnings:
        print(f"WARN   {warning}")
    for error in report.errors:
        print(f"ERROR  {error}")

    if report.errors:
        print()
        print(f"{len(report.errors)} problem(s) found.")
        return 1

    print()
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
