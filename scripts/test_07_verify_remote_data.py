# -*- coding: utf-8 -*-

"""
Verify that the remote PostgreSQL (NeonDB) database really holds the synced data.

This is the confirmation step after ``test_06_sync_data_to_remote_db.py``. That
script reports what it *believes* it wrote; this one goes back to the remote
database and checks what is actually there.

Remote tables carry the project prefix set in ``data/dataset.toml`` (local ``widget``
-> remote ``acme_widget``), so each local table is compared against its prefixed
counterpart. Tables belonging to other projects are ignored.

Three things are checked per table:

1. The prefixed table exists remotely.
2. It is not empty.
3. Its row count matches the local SQLite table it was synced from.

Checking against local counts is the point. A bare "is there data?" check passes
happily on a half-finished sync, which is the failure you actually care about --
the remote database is not empty, so nothing looks broken, but rows are missing.

Usage:
    .venv/bin/python scripts/test_07_verify_remote_data.py

Exit code is 0 when every table matches, 1 otherwise, so it can be used as a
gate in a deploy script.
"""

import sys

import sqlalchemy as sa

from agent_app.api import one
from agent_app.project_config import project_config
from agent_app.tests.db_sync import TABLE_INSERT_ORDER, prefixed


def count_rows(engine: sa.Engine, table_name: str) -> int:
    """
    Count the rows in one table.

    Args:
        engine: SQLAlchemy engine to query.
        table_name: Table to count. Built from the hardcoded TABLE_INSERT_ORDER
            list plus the configured prefix, never from user input, so
            interpolating it is safe here.

    Returns:
        The number of rows in the table.
    """
    with engine.connect() as conn:
        return conn.execute(
            sa.text(f'SELECT COUNT(*) FROM "{table_name}"')
        ).scalar_one()


def main() -> int:
    """
    Compare remote row counts against local, table by table.

    Returns:
        0 if every table exists and matches local, 1 otherwise.
    """
    local_engine = one.local_sqlite_engine
    remote_engine = one.remote_postgres_engine
    table_prefix = project_config.project_name_snake

    print("=" * 76)
    print("Verifying remote PostgreSQL data against local SQLite")
    print(f"Project prefix: {table_prefix}_")
    print("=" * 76)

    remote_tables = set(sa.inspect(remote_engine).get_table_names())

    rows = []
    problems = []

    for table_name in TABLE_INSERT_ORDER:
        remote_name = prefixed(table_prefix, table_name)
        local_count = count_rows(local_engine, table_name)

        if remote_name not in remote_tables:
            rows.append((remote_name, local_count, "MISSING", "table not found"))
            problems.append(f"{remote_name}: table does not exist remotely")
            continue

        remote_count = count_rows(remote_engine, remote_name)

        if remote_count == 0 and local_count > 0:
            status = "EMPTY"
            problems.append(f"{remote_name}: remote is empty, local has {local_count}")
        elif remote_count != local_count:
            status = "MISMATCH"
            problems.append(
                f"{remote_name}: remote has {remote_count}, local has {local_count}"
            )
        else:
            status = "OK"

        rows.append((remote_name, local_count, str(remote_count), status))

    # Print an aligned report rather than a bare dict: the whole value of this
    # script is being able to eyeball which table went wrong.
    width = max(len(name) for name, *_ in rows)
    print(f"{'remote table'.ljust(width)}  {'local':>8}  {'remote':>8}  status")
    print(f"{'-' * width}  {'-' * 8}  {'-' * 8}  ------")
    for remote_name, local_count, remote_count, status in rows:
        print(
            f"{remote_name.ljust(width)}  {local_count:>8}  {remote_count:>8}  {status}"
        )

    print("=" * 76)
    if problems:
        print(f"FAILED - {len(problems)} problem(s):")
        for problem in problems:
            print(f"  - {problem}")
        print("\nRe-run the sync with:")
        print("    .venv/bin/python scripts/test_06_sync_data_to_remote_db.py")
        print("=" * 76)
        return 1

    total = sum(local_count for _, local_count, _, _ in rows)
    print(f"OK - all {len(rows)} tables match local ({total:,} rows total).")
    print("=" * 76)
    return 0


if __name__ == "__main__":
    sys.exit(main())
