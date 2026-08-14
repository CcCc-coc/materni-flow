# -*- coding: utf-8 -*-

"""
Preflight check: is this repo internally consistent with its own config?

Why this script exists
----------------------

This repo is a template. The same scaffolding — one prompt, one database, one
website — gets pointed at a new dataset and a new business domain over and over.
Most of what changes is now centralized in ``config/dataset.toml`` and
``config/site.ts``, but not all of it can be: the SQLite file, the system prompt, and the kickstart questions are
content, not configuration, and they have to be rewritten by hand.

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
3. **Content files** — the system prompt and the kickstart questions must exist
   and be non-trivial.
4. **Retired vocabulary** — opt in with ``--retired``, for the one run right
   after a dataset swap.

Icon names used to be checked here too. They no longer need to be: the UI config
moved to ``config/site.ts``, where the ``IconName`` type makes a typo a compile
error instead of a silent fallback in the browser.

Usage::

    mise run check
    .venv/bin/python scripts/test_00_check_project_config.py
"""

import argparse
import json
import re
import sys
import typing as T
from pathlib import Path

import sqlalchemy as sa

from agent_app.paths import path_enum
from agent_app.project_config import project_config


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
    Fail if ``database.tableInsertOrder`` and the SQLite file disagree.

    Both directions matter. A table in the database but missing from the list
    silently never reaches the remote deployment; a table in the list but
    missing from the database blows up mid-sync, halfway through writing.
    """
    configured = project_config.table_insert_order

    missing_from_config = sorted(db_tables - set(configured))
    missing_from_db = sorted(set(configured) - db_tables)

    for name in missing_from_config:
        report.error(
            "table-order",
            f"table {name!r} exists in the database but is absent from "
            f"database.tableInsertOrder — it would never sync to the remote DB.",
        )
    for name in missing_from_db:
        report.error(
            "table-order",
            f"database.tableInsertOrder lists {name!r}, which does not exist in "
            f"{path_enum.path_sqlite_db.name} — the sync would fail on it.",
        )

    ok = not missing_from_config and not missing_from_db
    report.section(f"table insert order ({len(configured)} tables)", ok)
    return ok


def check_prompt_tables(report: Report, db_tables: set[str]) -> bool:
    """
    Fail if the system prompt queries a table the database does not have.

    Scans for identifiers following ``FROM`` and ``JOIN`` in the prompt's SQL
    examples. A prompt that teaches the agent to query a table left behind by the
    previous dataset produces confident, entirely wrong SQL at runtime.

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
    referenced = set(
        name.lower()
        for name in re.findall(
            r"\b(?:FROM|JOIN)\s+([a-z_][a-z0-9_]*)",
            text,
            re.IGNORECASE,
        )
    )

    # CTEs the prompt defines itself: `WITH name AS (` and `, name AS (`.
    cte_names = set(
        name.lower()
        for name in re.findall(
            r"(?:\bWITH\s+|,\s*)([a-z_][a-z0-9_]*)\s+AS\s*\(",
            text,
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

    prompt = path_enum.path_bi_agent_system_prompt_md
    if not prompt.exists():
        report.error("content", f"system prompt missing: {prompt}")
        ok = False
    elif len(prompt.read_text(encoding="utf-8").strip()) < 500:
        report.error("content", f"system prompt looks like a stub: {prompt}")
        ok = False

    suggestions = path_enum.dir_project_root / "data" / "suggested-actions.json"
    if not suggestions.exists():
        report.error("content", f"kickstart questions missing: {suggestions}")
        ok = False
    else:
        actions = json.loads(suggestions.read_text(encoding="utf-8"))
        if not actions:
            report.error("content", "data/suggested-actions.json is empty")
            ok = False
        else:
            for i, action in enumerate(actions):
                missing = {"title", "label", "action"} - set(action)
                if missing:
                    report.error(
                        "content",
                        f"data/suggested-actions.json[{i}] is missing {sorted(missing)}",
                    )
                    ok = False

    report.section("content files", ok)
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
