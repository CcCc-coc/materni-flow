# -*- coding: utf-8 -*-

"""
Everything that gets a dataset from its generator into the database.

**This module is teaching material and is meant to be deleted.** Nothing on the
production path imports it: the agent reads PostgreSQL through ``one.engine``,
and how the rows got there is not its problem. Deleting this file, the top-level
``dataset/`` directory and the ``gen-data`` / ``sync-db`` tasks removes the whole
authoring story and leaves a working app pointed at an already-populated
database.

That is also why ``dataset/requirements.txt`` is separate from ``pyproject.toml``:
the generator's dependencies are not the app's.

    dataset/04-*_data_generator*.py          the lesson artifact
            |  generate_dataset()
            v
    dataset/<name>.sqlite                    gitignored, discovered not named
            |  sync_sqlite_to_postgres()
            v
    PostgreSQL schema <SCHEMA_NAME>          the only thing the agent reads

There is no working copy in ``tmp/`` any more. It existed to protect a committed
seed from mutation; the seed is neither committed nor precious now -- rebuilding
it is one command.
"""

import typing as T
import shutil
import warnings
import subprocess
from pathlib import Path

import sqlalchemy as sa

from .paths import path_enum
from .sql_utils import new_sqlite_engine

#: The dataset's own directory: source documents, the generator, and the
#: generator's output. Committed except for the output.
DIR_DATASET = path_enum.dir_project_root / "dataset"


#: How to rebuild the database, quoted in the errors that need it. The teaching
#: CLI lives with the skill that documents it, not in ``mise.toml`` -- mise runs
#: the app, and none of this is the app.
GEN_HINT = (
    ".venv/bin/python .claude/skills/about-bi-agent-app-scaffold-cn"
    "/scripts/teaching_cli.py gen-data"
)


def _run(argv: list[str], step: str, verbose: bool = True) -> None:
    """Run one subprocess from the project root, letting its output through."""
    if verbose:
        print(f"[{step}] {' '.join(argv)}")
    subprocess.run(argv, check=True, cwd=path_enum.dir_project_root)


def _find_one(pattern: str, what: str, fix: str) -> Path:
    """
    The single file in ``dataset/`` matching ``pattern``.

    Discovered rather than named because the filenames belong to the dataset,
    and naming them here would make a swap edit ``agent_app/``.

    Zero matches and several matches both raise. Picking one silently is how the
    wrong dataset gets served.
    """
    found = sorted(DIR_DATASET.glob(pattern))
    if not found:
        raise FileNotFoundError(f"No {what} in {DIR_DATASET} (looked for {pattern!r}). {fix}")
    if len(found) > 1:
        names = ", ".join(p.name for p in found)
        raise RuntimeError(
            f"{DIR_DATASET} holds more than one {what}: {names}. One repository "
            f"serves one dataset; delete the ones you are not using."
        )
    return found[0]


def dataset_sqlite_files() -> list[Path]:
    """
    Every ``.sqlite`` in ``dataset/``, without judging how many there are.

    :func:`path_dataset_sqlite` is the one that insists on exactly one; callers
    that are about to *build* the database need to look without raising first.
    """
    return sorted(DIR_DATASET.glob("*.sqlite"))


def path_dataset_sqlite() -> Path:
    """The database the generator built. Not committed -- it is regenerated."""
    return _find_one("*.sqlite", "dataset database", f"Build it with `{GEN_HINT}`.")


def path_dataset_generator() -> Path:
    """The generator script that builds the database from faked data."""
    return _find_one(
        "*data_generator*.py", "dataset generator", "It ships with the dataset."
    )


def path_dataset_requirements() -> Path:
    """
    The generator's dependencies, deliberately apart from ``pyproject.toml``.

    A fixed name rather than a discovered one: unlike the database and the
    generator, this filename is ours, not the dataset's.
    """
    path = DIR_DATASET / "requirements.txt"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} is missing. It lists what the dataset's generator needs, "
            f"which is not the same as what the app needs."
        )
    return path


def local_sqlite_engine() -> sa.Engine:
    """
    An engine over the generated database.

    Opened through :func:`~agent_app.sql_utils.new_sqlite_engine` so the
    read-only guarantee holds on it -- see that function for why SQLite needs
    help with it.
    """
    return new_sqlite_engine(str(path_dataset_sqlite()))


def install_generator_requirements(verbose: bool = True) -> None:
    """
    Install the generator's dependencies into this project's venv.

    Through ``uv``, because ``uv venv`` does not put ``pip`` in the venv -- there
    is no ``.venv/bin/pip`` to call. uv is already required to install the app
    itself, so this adds no new tool.

    Into the project venv rather than one of its own: it is a handful of packages
    used by one script, and a second environment costs more to explain than it
    saves. They stay listed apart from ``pyproject.toml`` so that deleting the
    teaching layer takes them with it.
    """
    if shutil.which("uv") is None:
        raise RuntimeError(
            "uv is not on PATH, and this venv has no pip of its own to fall back "
            "on. Install uv (https://docs.astral.sh/uv/), or install "
            f"{path_dataset_requirements()} by hand."
        )
    _run(
        [
            "uv", "pip", "install",
            "--python", str(path_enum.path_venv_python),
            "-r", str(path_dataset_requirements()),
        ],
        "deps",
        verbose,
    )


def generate_dataset(force: bool = False, verbose: bool = True) -> Path:
    """
    Build the dataset's database by running the generator that ships with it.

    **Does nothing when the database already exists**, because generating takes
    minutes and the common case is that it is already there. ``force`` is how you
    say you meant it.

    ``force`` also *deletes every* ``.sqlite`` in ``dataset/`` first. That is not
    housekeeping: a leftover file from a previous dataset would make
    :func:`path_dataset_sqlite` refuse to choose, and the run that just rebuilt
    the right one would look broken.

    :param force: Rebuild even if a database is already there.
    :raises subprocess.CalledProcessError: if a step fails. Both steps stream
        their own output, so the reason is already on screen.
    """
    existing = dataset_sqlite_files()

    if existing and not force:
        if verbose:
            print(f"Database already exists, keeping it: {existing[0]}")
            print("Pass force=True (or --force) to rebuild from scratch.")
        return existing[0]

    for stale in existing:
        if verbose:
            print(f"Removing {stale.name}")
        stale.unlink()

    install_generator_requirements(verbose=verbose)
    _run([str(path_enum.path_venv_python), str(path_dataset_generator())], "generate", verbose)

    built = path_dataset_sqlite()
    if verbose:
        print(f"Database ready at: {built} ({built.stat().st_size:,} bytes)")
    return built


def table_insert_order(metadata: "sa.MetaData") -> list[str]:
    """
    Table names in foreign-key dependency order: parents first, drops reversed.

    Computed, never configured. A hand-copied topological sort is a value that
    can be wrong; ``metadata.sorted_tables`` cannot be.

    A foreign-key cycle admits no insert order, and SQLAlchemy only *warns*
    about one -- it returns a list with those constraints ignored, which would
    sync silently and fail on the first insert. Promoting the warning is what
    makes this function's promise true.

    :raises RuntimeError: on a foreign-key cycle.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("error", sa.exc.SAWarning)
        try:
            return [table.name for table in metadata.sorted_tables]
        except sa.exc.SAWarning as e:
            raise RuntimeError(
                f"The dataset's foreign keys form a cycle, so no insert order "
                f"can satisfy them: {e}"
            ) from e


#: Rows per executemany round trip. Sending a six-figure table in one statement
#: risks exceeding the driver's parameter limit and buffers the whole table in
#: memory; one row per round trip is unusably slow over a network.
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

    """
    remote_metadata = sa.MetaData(schema=schema_name)

    for table_name in table_insert_order(local_metadata):
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

    insert_order = table_insert_order(local_metadata)
    if not insert_order:
        raise ValueError(
            f"{path_dataset_sqlite()} has no tables. Rebuild it with "
            f"`{GEN_HINT}`."
        )
    log(f"  {len(insert_order)} tables, dependency order: {', '.join(insert_order)}")

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
        for table_name in insert_order:
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
        for table_name in reversed(insert_order):
            qualified = f'"{schema_name}"."{table_name}"'
            conn.execute(sa.text(f"DROP TABLE IF EXISTS {qualified}{cascade}"))
            log(f"  Dropped: {table_name}")

    # Step 4: Recreate them, same names, inside the schema.
    log("Creating remote tables...")
    remote_metadata = build_remote_metadata(local_metadata, schema_name)
    remote_metadata.create_all(remote_engine)
    log(f"  Created {len(insert_order)} tables.")

    # Step 5: Insert, parents first, batched.
    log("Inserting data into remote PostgreSQL...")
    summary = {}
    with remote_engine.begin() as conn:
        for table_name in insert_order:
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

    Takes ``remote_postgres_engine`` (unscoped) rather than ``engine`` (pinned
    to our schema): the sync creates that schema, so it cannot assume it is
    already there to be pinned to.
    """
    from agent_app.one.api import one

    return sync_sqlite_to_postgres(
        local_engine=local_sqlite_engine(),
        remote_engine=one.remote_postgres_engine,
        schema_name=one.config.schema_name,
        verbose=verbose,
    )
