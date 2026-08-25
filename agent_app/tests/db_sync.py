# -*- coding: utf-8 -*-

"""
Database sync utilities: push the local SQLite database to remote PostgreSQL.

Table name prefixing
--------------------

The remote NeonDB instance is shared between several projects, so every table
this project owns is namespaced with the project name::

    local SQLite          remote PostgreSQL
    ------------          -----------------
    widget          ->    acme_widget
    part            ->    acme_part

The prefix comes from ``project_config.project_name_snake``. Foreign keys are rewritten
to match, so ``widget.part_id -> part.id`` becomes
``acme_widget.part_id -> acme_part.id``. Nothing in the remote database
refers to an unprefixed name.

Ordering
--------

``TABLE_INSERT_ORDER`` is the single source of truth for dependency order:
parents first, children after. It is not written here — it comes from
``data/dataset.toml``, so that swapping the dataset means editing one TOML file
rather than hunting for a list buried in a sync module. Everything else is
derived from it —

- **inserting** walks the list forwards, so a row's parents already exist;
- **dropping** walks it backwards, so no table is dropped while another still
  references it.

Deriving both directions from one list is what keeps them from drifting apart.
"""

import typing as T

import sqlalchemy as sa

from ..project_config import project_config

#: Table insertion order based on foreign key dependencies: parents first, so a
#: row's parents already exist by the time it is inserted. Drop order is the
#: reverse — see the module docstring.
#:
#: Defined in ``data/dataset.toml`` under ``database.tableInsertOrder``.
#: ``mise run check`` verifies it against the tables actually present in
#: ``data/data.sqlite.example``, so a table added to the dataset but forgotten here
#: fails loudly instead of silently vanishing from the remote database.
TABLE_INSERT_ORDER = project_config.table_insert_order

#: Rows per executemany round trip. Sending a six-figure table in one
#: statement risks exceeding the driver's parameter limit and buffers the whole
#: table in memory; one row per round trip is unusably slow over a network.
INSERT_BATCH_SIZE = 1000


def prefixed(table_prefix: str, table_name: str) -> str:
    """
    Build the remote table name for a local table.

    Args:
        table_prefix: Project prefix, e.g. ``"acme"``. Empty string means no
            prefixing, which is useful in tests.
        table_name: Local table name, e.g. ``"widget"``.

    Returns:
        The remote table name, e.g. ``"acme_widget"``.
    """
    if not table_prefix:
        return table_name
    return f"{table_prefix}_{table_name}"


def to_postgres_type(col_type: T.Any) -> T.Any:
    """
    Map a reflected SQLite column type onto a PostgreSQL-friendly equivalent.

    SQLite's type affinity is loose — reflection hands back things like
    ``VARCHAR(50)`` or ``DECIMAL(12, 2)`` that either do not exist or behave
    differently in PostgreSQL. Normalizing here keeps the created schema
    predictable instead of depending on whatever the source file happened to say.

    Args:
        col_type: The reflected SQLAlchemy type.

    Returns:
        A SQLAlchemy type to use for the remote column.
    """
    type_str = str(col_type).upper()

    if "DATETIME" in type_str:
        return sa.TIMESTAMP()
    if "DATE" in type_str:
        return sa.Date()
    if "DECIMAL" in type_str or "NUMERIC" in type_str:
        return sa.Numeric()
    if "BOOLEAN" in type_str:
        return sa.Boolean()
    if isinstance(col_type, sa.TEXT) or "TEXT" in type_str:
        return sa.Text()
    if isinstance(col_type, sa.INTEGER) or "INTEGER" in type_str or "INT" in type_str:
        return sa.Integer()
    if isinstance(col_type, sa.REAL) or "REAL" in type_str or "FLOAT" in type_str:
        return sa.Float()
    if isinstance(col_type, sa.BLOB):
        return sa.LargeBinary()
    if "VARCHAR" in type_str:
        # TEXT for every VARCHAR: PostgreSQL TEXT performs identically and this
        # avoids inheriting length limits that SQLite never enforced anyway.
        return sa.Text()
    return col_type


def build_remote_metadata(
    local_metadata: sa.MetaData,
    table_prefix: str,
) -> sa.MetaData:
    """
    Build the prefixed remote schema from the reflected local schema.

    Both the table names and the foreign key targets are prefixed, so the remote
    schema is internally consistent and never points at an unprefixed table.

    Args:
        local_metadata: Metadata reflected from the local SQLite database.
        table_prefix: Project prefix, e.g. ``"acme"``.

    Returns:
        A new MetaData holding the prefixed tables, ready for ``create_all()``.
    """
    remote_metadata = sa.MetaData()

    # The local file and `data/dataset.toml` can disagree — most often because
    # `tmp/data.sqlite` is left over from a different dataset and nobody re-ran
    # `mise run setup-db` after a swap. Reported as a bare KeyError on whichever
    # table happened to be missing, that costs a real debugging session before
    # anyone suspects the seed file. Name the actual problem instead.
    missing = [t for t in TABLE_INSERT_ORDER if t not in local_metadata.tables]
    if missing:
        raise ValueError(
            f"Local database is missing {len(missing)} table(s) named in "
            f"data/dataset.toml: {', '.join(missing)}. "
            f"It holds {sorted(local_metadata.tables)} instead. "
            f"If this file is left over from another dataset, re-seed it with "
            f"`mise run setup-db`; otherwise fix `database.tableInsertOrder`."
        )

    for table_name in TABLE_INSERT_ORDER:
        local_table = local_metadata.tables[table_name]
        new_columns = []

        for col in local_table.columns:
            # Repoint each FK at the prefixed name of the table it references.
            foreign_keys = [
                sa.ForeignKey(
                    f"{prefixed(table_prefix, fk.column.table.name)}.{fk.column.name}"
                )
                for fk in col.foreign_keys
            ]
            new_columns.append(
                sa.Column(
                    col.name,
                    to_postgres_type(col.type),
                    *foreign_keys,
                    primary_key=col.primary_key,
                    nullable=col.nullable,
                )
            )

        sa.Table(prefixed(table_prefix, table_name), remote_metadata, *new_columns)

    return remote_metadata


def sync_sqlite_to_postgres(
    local_engine: sa.Engine,
    remote_engine: sa.Engine,
    table_prefix: str,
    verbose: bool = True,
    batch_size: int = INSERT_BATCH_SIZE,
) -> dict:
    """
    Sync the local SQLite database to the remote PostgreSQL database.

    Idempotent: every run drops the project's remote tables and rebuilds them, so
    the remote database ends up as an exact copy of local regardless of what was
    there before.

    Only tables carrying ``table_prefix`` are touched. Tables belonging to other
    projects in the same database are left alone — that is the entire point of
    the prefix.

    Args:
        local_engine: Engine connected to the local SQLite database.
        remote_engine: Engine connected to the remote PostgreSQL database.
        table_prefix: Project prefix for remote table names, e.g. ``"acme"``.
        verbose: If True, print progress messages.
        batch_size: Rows per executemany round trip.

    Returns:
        dict: ``{"success": True, "table_prefix": ..., "tables": {remote_name: row_count}}``

    Raises:
        ValueError: If the local database is missing an expected table.
    """

    def log(msg: str):
        if verbose:
            print(msg)

    log(f"Syncing local SQLite -> remote PostgreSQL (prefix: {table_prefix!r})")

    # Step 1: Reflect the local schema.
    log("Reflecting local SQLite schema...")
    local_metadata = sa.MetaData()
    local_metadata.reflect(bind=local_engine)

    local_table_names = set(local_metadata.tables.keys())
    missing_tables = set(TABLE_INSERT_ORDER) - local_table_names
    if missing_tables:
        raise ValueError(
            f"Missing tables in local database: {sorted(missing_tables)}. "
            f"Re-seed it with: mise run setup-db"
        )

    extra_tables = local_table_names - set(TABLE_INSERT_ORDER)
    if extra_tables:
        log(f"  Warning: extra local tables, will be ignored: {sorted(extra_tables)}")

    # Step 2: Read every row out of local, in dependency order.
    #
    # Select through the reflected Table rather than raw SQL text: that runs the
    # column type processors, so a DATE arrives as a `datetime.date` and a
    # BOOLEAN as a real bool instead of the string / 0-1 integer SQLite stores.
    # Raw `SELECT *` text skips those processors, and the untyped values it
    # returns are then rejected on the way into the typed remote columns.
    log("Reading data from local SQLite...")
    local_data = {}
    with local_engine.connect() as conn:
        for table_name in TABLE_INSERT_ORDER:
            local_table = local_metadata.tables[table_name]
            result = conn.execute(sa.select(local_table))
            rows = [dict(row._mapping) for row in result]
            local_data[table_name] = rows
            log(f"  {table_name}: {len(rows)} rows")

    # Step 3: Drop this project's remote tables, children first.
    #
    # CASCADE also clears dependent objects outside our table set (a view someone
    # built on top of these, say). It is PostgreSQL-only syntax, hence the guard —
    # which is also what lets this function be tested against a SQLite stand-in.
    cascade = " CASCADE" if remote_engine.dialect.name == "postgresql" else ""
    log("Dropping remote tables (reverse dependency order)...")
    with remote_engine.begin() as conn:
        for table_name in reversed(TABLE_INSERT_ORDER):
            remote_name = prefixed(table_prefix, table_name)
            conn.execute(sa.text(f'DROP TABLE IF EXISTS "{remote_name}"{cascade}'))
            log(f"  Dropped: {remote_name}")

    # Step 4: Recreate them with prefixed names and prefixed FK targets.
    log("Creating remote tables...")
    remote_metadata = build_remote_metadata(local_metadata, table_prefix)
    remote_metadata.create_all(remote_engine)
    log(f"  Created {len(TABLE_INSERT_ORDER)} tables.")

    # Step 5: Insert, parents first, batched.
    log("Inserting data into remote PostgreSQL...")
    summary = {}
    with remote_engine.begin() as conn:
        for table_name in TABLE_INSERT_ORDER:
            remote_name = prefixed(table_prefix, table_name)
            rows = local_data[table_name]

            if not rows:
                log(f"  {remote_name}: 0 rows (empty)")
                summary[remote_name] = 0
                continue

            insert_stmt = sa.insert(remote_metadata.tables[remote_name])
            for start in range(0, len(rows), batch_size):
                # Passing a list of dicts makes this one executemany per batch
                # instead of one round trip per row.
                conn.execute(insert_stmt, rows[start : start + batch_size])

            log(f"  {remote_name}: {len(rows)} rows")
            summary[remote_name] = len(rows)

    log("Sync completed successfully!")
    return {"success": True, "table_prefix": table_prefix, "tables": summary}


def reset_remote_database(verbose: bool = True) -> dict:
    """
    Reset the remote database by syncing from local SQLite.

    Convenience wrapper that pulls both engines and the project prefix off the
    ``One`` singleton.

    Args:
        verbose: If True, print progress messages.

    Returns:
        dict: Summary of the sync operation.
    """
    from agent_app.one.api import one

    return sync_sqlite_to_postgres(
        local_engine=one.local_sqlite_engine,
        remote_engine=one.remote_postgres_engine,
        table_prefix=project_config.project_name_snake,
        verbose=verbose,
    )


def setup_remote_database():
    """Reset database before running tests."""
    print("Resetting database...")
    reset_remote_database(verbose=False)
    print("Database reset complete.\n")
