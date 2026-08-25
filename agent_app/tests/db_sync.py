# -*- coding: utf-8 -*-

"""
Database sync utilities: push the local SQLite database to remote PostgreSQL.

The namespace is a schema, not a prefix
---------------------------------------

The remote NeonDB instance is shared between several projects, so this project's
tables have to be namespaced. They are namespaced with a **schema**, and the
table names are identical on both sides::

    local SQLite          remote PostgreSQL
    ------------          -----------------
    widget          ->    schema acme_widgets.widget
    part            ->    schema acme_widgets.part

**The table names being identical is the entire design goal.** An earlier
revision namespaced with a table-name prefix (``acme_widget``) and it failed
that test: the schema string the agent reads, and therefore every SQL example in
the system prompt, came out different depending on which engine was behind it --
correct in one environment, wrong in the other, with nothing to catch it. A
schema moves the namespace off the table name, so the name the agent sees never
changes.

Foreign keys are re-pointed into the same schema, so the target is
self-contained and never reaches across into another project's tables.

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
    schema_name: str,
) -> sa.MetaData:
    """
    Build the remote schema from the reflected local schema.

    Table names are copied unchanged -- only the schema they sit in differs.
    Foreign keys are re-pointed into the same schema, so the remote copy is
    self-contained.

    Args:
        local_metadata: Metadata reflected from the local SQLite file.
        schema_name: The PostgreSQL schema to build into.

    Returns:
        A new MetaData bound to ``schema_name``, ready for ``create_all()``.

    Raises:
        ValueError: If the source file lacks a table the config names.
    """
    remote_metadata = sa.MetaData(schema=schema_name)

    # The source file and dataset.toml can disagree -- most often because the
    # data generator was re-run after a schema change and nobody updated
    # `tableInsertOrder`. Reported as a bare KeyError on whichever table happened
    # to be missing, that costs a real debugging session before anyone suspects
    # the config. Name the actual problem instead.
    missing = [t for t in TABLE_INSERT_ORDER if t not in local_metadata.tables]
    if missing:
        raise ValueError(
            f"Source database is missing {len(missing)} table(s) named in "
            f"data/dataset.toml: {', '.join(missing)}. "
            f"It holds {sorted(local_metadata.tables)} instead. "
            f"Rebuild it from the dataset's data generator, or fix "
            f"`database.tableInsertOrder`."
        )

    for table_name in TABLE_INSERT_ORDER:
        local_table = local_metadata.tables[table_name]
        new_columns = []

        for col in local_table.columns:
            # Repoint each FK into the target schema. The table name is
            # unchanged; only the schema qualifier is added.
            foreign_keys = [
                sa.ForeignKey(f"{schema_name}.{fk.column.table.name}.{fk.column.name}")
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

        sa.Table(table_name, remote_metadata, *new_columns)

    return remote_metadata


def sync_sqlite_to_postgres(
    local_engine: sa.Engine,
    remote_engine: sa.Engine,
    schema_name: str,
    verbose: bool = True,
    batch_size: int = INSERT_BATCH_SIZE,
) -> dict:
    """
    Sync the local SQLite database into this project's remote schema.

    Idempotent: every run drops this project's tables and rebuilds them, so the
    remote schema ends up an exact copy of local regardless of what was there
    before.

    Only ``schema_name`` is touched. Other projects live in other schemas and
    are never named by anything here -- that is the entire point of using a
    schema.

    Args:
        local_engine: Engine connected to the local SQLite database.
        remote_engine: Engine on the shared database. Must **not** be pinned to
            a schema: this function creates the schema and writes fully
            qualified names, and a pinned ``search_path`` would only confuse
            that.
        schema_name: The PostgreSQL schema to publish into.
        verbose: If True, print progress messages.
        batch_size: Rows per executemany round trip.

    Returns:
        dict: ``{"success": True, "schema": ..., "tables": {name: row_count}}``

    Raises:
        ValueError: If the local database is missing an expected table.
    """

    def log(msg: str):
        if verbose:
            print(msg)

    log(f"Syncing local SQLite -> remote PostgreSQL (schema: {schema_name!r})")

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

    # Step 3: Make sure the schema exists, then drop this project's tables
    # inside it, children first.
    #
    # CASCADE also clears dependent objects outside our table set (a view someone
    # built on top of these, say). It is PostgreSQL-only syntax, hence the guard —
    # which is also what lets this function be tested against a SQLite stand-in.
    is_postgres = remote_engine.dialect.name == "postgresql"
    cascade = " CASCADE" if is_postgres else ""
    with remote_engine.begin() as conn:
        if is_postgres:
            conn.execute(sa.schema.CreateSchema(schema_name, if_not_exists=True))
            log(f"Schema ready: {schema_name}")

        log("Dropping remote tables (reverse dependency order)...")
        for table_name in reversed(TABLE_INSERT_ORDER):
            qualified = f'"{schema_name}"."{table_name}"'
            conn.execute(sa.text(f"DROP TABLE IF EXISTS {qualified}{cascade}"))
            log(f"  Dropped: {table_name}")

    # Step 4: Recreate them, same names, inside the schema.
    log("Creating remote tables...")
    remote_metadata = build_remote_metadata(local_metadata, schema_name)
    remote_metadata.create_all(remote_engine)
    log(f"  Created {len(TABLE_INSERT_ORDER)} tables.")

    # Step 5: Insert, parents first, batched.
    log("Inserting data into remote PostgreSQL...")
    summary = {}
    with remote_engine.begin() as conn:
        for table_name in TABLE_INSERT_ORDER:
            rows = local_data[table_name]

            if not rows:
                log(f"  {table_name}: 0 rows (empty)")
                summary[table_name] = 0
                continue

            insert_stmt = sa.insert(remote_metadata.tables[f"{schema_name}.{table_name}"])
            for start in range(0, len(rows), batch_size):
                # Passing a list of dicts makes this one executemany per batch
                # instead of one round trip per row.
                conn.execute(insert_stmt, rows[start : start + batch_size])

            log(f"  {table_name}: {len(rows)} rows")
            summary[table_name] = len(rows)

    log("Sync completed successfully!")
    return {"success": True, "schema": schema_name, "tables": summary}


def reset_remote_database(verbose: bool = True) -> dict:
    """
    Reset the remote database by syncing from local SQLite.

    Convenience wrapper that pulls both engines and the schema name off the
    ``One`` singleton. Note it takes ``remote_postgres_engine`` (unscoped)
    rather than ``engine`` (pinned to our schema): the sync creates that schema,
    so it cannot assume it is already there to be pinned to.

    Args:
        verbose: If True, print progress messages.

    Returns:
        dict: Summary of the sync operation.
    """
    from agent_app.one.api import one

    return sync_sqlite_to_postgres(
        local_engine=one.local_sqlite_engine,
        remote_engine=one.remote_postgres_engine,
        schema_name=project_config.schema_name,
        verbose=verbose,
    )


def setup_remote_database():
    """Reset database before running tests."""
    print("Resetting database...")
    reset_remote_database(verbose=False)
    print("Database reset complete.\n")
