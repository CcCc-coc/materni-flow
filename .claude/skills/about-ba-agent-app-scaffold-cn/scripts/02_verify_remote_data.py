# -*- coding: utf-8 -*-

"""
Verify that the remote PostgreSQL (NeonDB) database really holds the synced data.

This is the confirmation step after ``01_sync_data_to_remote_db.py``. That
script reports what it *believes* it wrote; this one goes back to the remote
database and checks what is actually there.

Remote tables live in the PostgreSQL schema named by ``SCHEMA_NAME`` in ``.env.defaults`` and
carry the same names as the local ones, so each local table is compared against
its namesake inside that schema. Other projects live in other schemas and are
never looked at.

Three things are checked per table:

1. The table exists remotely, inside this project's schema.
2. It is not empty.
3. Its row count matches the local SQLite table it was synced from.

Checking against local counts is the point. A bare "is there data?" check passes
happily on a half-finished sync, which is the failure you actually care about --
the remote database is not empty, so nothing looks broken, but rows are missing.

Run it through the teaching CLI sitting next to this file:
    .venv/bin/python <this skill>/scripts/teaching_cli.py verify-db

Exit code is 0 when every table matches, 1 otherwise, so it can be used as a
gate in a deploy script.
"""

import sys

import sqlalchemy as sa

from agent_app.api import one
from agent_app.dataset import local_sqlite_engine, table_insert_order


def count_rows(engine: sa.Engine, table_name: str, schema: str | None = None) -> int:
    """
    Count the rows in one table.

    Args:
        engine: SQLAlchemy engine to query.
        table_name: Table to count. Reflected from the local database, never
            from user input, so interpolating it is safe here.
        schema: The PostgreSQL schema it lives in. ``None`` for local SQLite,
            which has no schemas.

    Returns:
        The number of rows in the table.
    """
    qualified = f'"{schema}"."{table_name}"' if schema else f'"{table_name}"'
    with engine.connect() as conn:
        return conn.execute(sa.text(f"SELECT COUNT(*) FROM {qualified}")).scalar_one()


def main() -> int:
    """
    Compare remote row counts against local, table by table.

    Returns:
        0 if every table exists and matches local, 1 otherwise.
    """
    local_engine = local_sqlite_engine()
    remote_engine = one.remote_postgres_engine
    schema_name = one.config.schema_name

    local_metadata = sa.MetaData()
    local_metadata.reflect(bind=local_engine)
    tables = table_insert_order(local_metadata)

    print("=" * 76)
    print("Verifying remote PostgreSQL data against local SQLite")
    print(f"PostgreSQL schema: {schema_name}")
    print("=" * 76)

    remote_tables = set(sa.inspect(remote_engine).get_table_names(schema=schema_name))

    rows = []
    problems = []

    for table_name in tables:
        local_count = count_rows(local_engine, table_name)

        if table_name not in remote_tables:
            rows.append((table_name, local_count, "MISSING", "table not found"))
            problems.append(f"{table_name}: table does not exist remotely")
            continue

        remote_count = count_rows(remote_engine, table_name, schema=schema_name)

        if remote_count == 0 and local_count > 0:
            status = "EMPTY"
            problems.append(f"{table_name}: remote is empty, local has {local_count}")
        elif remote_count != local_count:
            status = "MISMATCH"
            problems.append(
                f"{table_name}: remote has {remote_count}, local has {local_count}"
            )
        else:
            status = "OK"

        rows.append((table_name, local_count, str(remote_count), status))

    # Print an aligned report rather than a bare dict: the whole value of this
    # script is being able to eyeball which table went wrong.
    width = max(len(name) for name, *_ in rows)
    print(f"{'remote table'.ljust(width)}  {'local':>8}  {'remote':>8}  status")
    print(f"{'-' * width}  {'-' * 8}  {'-' * 8}  ------")
    for table_name, local_count, remote_count, status in rows:
        print(
            f"{table_name.ljust(width)}  {local_count:>8}  {remote_count:>8}  {status}"
        )

    print("=" * 76)
    if problems:
        print(f"FAILED - {len(problems)} problem(s):")
        for problem in problems:
            print(f"  - {problem}")
        print("\nRe-run the sync with:")
        print("    .venv/bin/python <this skill>/scripts/teaching_cli.py sync-db")
        print("=" * 76)
        return 1

    total = sum(local_count for _, local_count, _, _ in rows)
    print(f"OK - all {len(rows)} tables match local ({total:,} rows total).")
    print("=" * 76)
    return 0


if __name__ == "__main__":
    sys.exit(main())
