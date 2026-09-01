# -*- coding: utf-8 -*-

"""
Measure how much the compact encoding actually saves, on this dataset.

Compares the string the agent is shown against the plain CREATE TABLE DDL for
the same ten tables, which ships in the dataset's ER document.

    .venv/bin/python examples/22-encode-the-schema-for-llm/01_measure_the_encoding.py

Needs a synced database, because the encoding is built by reflecting the real
schema rather than by reading a file.
"""

import re

from agent_app.api import one
from agent_app.dataset import DIR_DATASET


def load_reference_ddl() -> str:
    """The CREATE TABLE block from the dataset's ER document, fences stripped."""
    doc = next(DIR_DATASET.glob("02-*_er_document*.md")).read_text(encoding="utf-8")
    match = re.search(r"## .*?SQLite DDL\)(.*?)\n## ", doc, re.S)
    if match is None:
        raise SystemExit("Could not find the DDL block in the ER document.")
    return "\n".join(
        line for line in match.group(1).split("\n") if not line.strip().startswith("```")
    )


def main() -> None:
    encoded = one.database_schema_str
    ddl = load_reference_ddl()

    print(f"{'':14}{'characters':>12}{'lines':>8}")
    print(f"{'encoded':14}{len(encoded):>12,}{len(encoded.splitlines()):>8}")
    print(f"{'plain DDL':14}{len(ddl):>12,}{len(ddl.splitlines()):>8}")
    print()
    print(f"encoded is {len(encoded) / len(ddl):.0%} the size, so it saves "
          f"{1 - len(encoded) / len(ddl):.0%}.")
    print()
    print("Characters, not tokens -- close enough to judge the shape, and it")
    print("needs no tokenizer. And the number depends entirely on what you")
    print("compare against: this DDL is already terse.")


if __name__ == "__main__":
    main()
