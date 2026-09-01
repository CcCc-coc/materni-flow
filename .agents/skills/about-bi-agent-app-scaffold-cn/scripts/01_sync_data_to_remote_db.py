# -*- coding: utf-8 -*-

"""
Sync local SQLite database to remote PostgreSQL (NeonDB).

Remote tables live in the PostgreSQL schema named by ``SCHEMA_NAME`` in
``.env.defaults``, so this project can share one NeonDB instance with others
without colliding. **Table names are identical on both sides**; only the schema
differs, and foreign keys are rewritten into it.

This script is DESTRUCTIVE and idempotent - each run will:
1. DROP this project's prefixed tables in reverse dependency order
2. CREATE them again with prefixed names and prefixed FK references
3. INSERT all data from local, in dependency order, in batches

Tables belonging to other projects are never touched.

Run it through the teaching CLI sitting next to this file:
    .venv/bin/python <this skill>/scripts/teaching_cli.py sync-db

Verify the result afterwards with:
    .venv/bin/python <this skill>/scripts/teaching_cli.py verify-db

It lives in the teaching layer rather than the repo's top-level ``scripts/``
because publishing deletes this directory, and a step that builds the dataset
has no business surviving that.
"""

from agent_app.api import one
from agent_app.dataset import reset_remote_database


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
    print("Now verify with: teaching_cli.py verify-db")


if __name__ == "__main__":
    main()
