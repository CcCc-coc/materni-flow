# -*- coding: utf-8 -*-

"""
Prove the read-only guarantee is the rollback, not the string check.

Runs three statements through the same function the agent's SQL tool calls,
against the LOCAL SQLite seed, and counts the rows before and after each one:

1. a plain SELECT                  -- works
2. a bare UPDATE                   -- refused by the string check, never runs
3. an UPDATE hidden behind a CTE   -- passes the string check, RUNS, and is
                                      then rolled back

The third one is the point. `WITH` is an allowed opening keyword, because a
read-only agent legitimately writes CTEs all day. So the string check lets this
through -- and the row count is still unchanged afterwards, because the
transaction is never committed.

    .venv/bin/python examples/24-the-sql-tool/01_rollback_proves_it.py

Safe to run: it touches the local seed only, and the whole point is that
nothing it does survives. Rebuild the seed with gen-data --force if you ever
doubt it.
"""

import sqlalchemy as sa

from agent_app.dataset import local_sqlite_engine
from agent_app.sql_utils import execute_sql_query

ENGINE = local_sqlite_engine()

CASES = [
    ("a plain SELECT", "SELECT grade_code, interest_rate FROM risk_grade ORDER BY grade_code"),
    ("a bare UPDATE", "UPDATE risk_grade SET interest_rate = 99.0"),
    (
        "an UPDATE hidden behind a CTE",
        "WITH victim AS (SELECT id FROM risk_grade) "
        "UPDATE risk_grade SET interest_rate = 99.0 "
        "WHERE id IN (SELECT id FROM victim)",
    ),
]


def rate_of_grade_a() -> float:
    """Read one number straight from the file, bypassing the tool entirely."""
    with ENGINE.connect() as conn:
        return conn.execute(
            sa.text("SELECT interest_rate FROM risk_grade WHERE grade_code = 'A'")
        ).scalar_one()


def main() -> None:
    for label, sql in CASES:
        before = rate_of_grade_a()
        output = execute_sql_query(engine=ENGINE, sql=sql)
        after = rate_of_grade_a()

        first_line = output.strip().split("\n")[0]
        print(f"--- {label}")
        print(f"    tool said: {first_line[:70]}")
        print(f"    grade A interest_rate: {before} -> {after}", end="")
        print("   UNCHANGED" if before == after else "   *** CHANGED ***")
        print()

    print("The second case never reached the database. The third one did, and")
    print("still changed nothing -- that is the rollback, not the string check.")


if __name__ == "__main__":
    main()
