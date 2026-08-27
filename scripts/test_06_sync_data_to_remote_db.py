# -*- coding: utf-8 -*-

"""
Sync local SQLite database to remote PostgreSQL (NeonDB).

Remote tables live in the PostgreSQL schema named by ``SCHEMA_NAME`` in ``.env.defaults``, so
this project can share one NeonDB instance with others without colliding:
local ``widget`` becomes remote ``acme_widget``, and its foreign keys are rewritten
to match.

This script is DESTRUCTIVE and idempotent - each run will:
1. DROP this project's prefixed tables in reverse dependency order
2. CREATE them again with prefixed names and prefixed FK references
3. INSERT all data from local, in dependency order, in batches

Tables belonging to other projects are never touched.

Usage:
    .venv/bin/python scripts/test_06_sync_data_to_remote_db.py

Verify the result afterwards with:
    .venv/bin/python scripts/test_07_verify_remote_data.py
"""

from agent_app.api import one
from agent_app.tests.db_sync import reset_remote_database


def main():
    """Run the sync operation."""
    print("=" * 68)
    print("Syncing local SQLite to remote PostgreSQL (NeonDB)")
    print(f"PostgreSQL schema: {one.config.schema_name}")
    print("=" * 68)

    result = reset_remote_database(verbose=True)

    print("=" * 68)
    print("Summary:")
    for table_name, row_count in result["tables"].items():
        print(f"  {table_name}: {row_count:,} rows")
    print(f"  total: {sum(result['tables'].values()):,} rows")
    print("=" * 68)
    print("Now verify with: mise run verify-db")


if __name__ == "__main__":
    main()
