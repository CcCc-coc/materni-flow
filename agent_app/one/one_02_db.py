# -*- coding: utf-8 -*-

"""Database mixin for the One class."""

import typing as T
from functools import cached_property

import sqlalchemy as sa

from ..paths import path_enum
from ..constants import DbTypeEnum
from ..project_config import project_config
from ..db_schema.api import new_schema_info
from ..db_schema.api import new_database_info
from ..db_schema.api import encode_database_info
from ..sql_utils import execute_and_print_result

if T.TYPE_CHECKING:  # pragma: no cover
    from .one_00_main import One


class DbMixin:
    """Mixin providing database connection and query execution capabilities."""

    @cached_property
    def local_sqlite_engine(self: "One") -> sa.Engine:
        """
        Create a SQLite engine connected to the local database file.

        The two event listeners are what make the agent's read-only guarantee
        hold on SQLite. ``execute_and_print_result`` protects the data by always
        rolling back, which relies on a transaction actually being open -- and
        pysqlite decides that by sniffing the statement's first keyword. It does
        not recognise ``WITH``, so a CTE-prefixed write runs in autocommit and
        lands on disk with nothing to roll back.

        Turning ``isolation_level`` off stops the driver guessing, and emitting
        ``BEGIN`` ourselves means every statement -- CTE-prefixed writes and DDL
        included -- is inside a transaction that the caller can discard. This is
        the recipe from SQLAlchemy's own pysqlite notes.
        """
        engine = sa.create_engine(f"sqlite:///{path_enum.path_sqlite_db}")

        @sa.event.listens_for(engine, "connect")
        def _disable_pysqlite_implicit_begin(dbapi_connection, _):
            dbapi_connection.isolation_level = None

        @sa.event.listens_for(engine, "begin")
        def _emit_explicit_begin(connection):
            connection.exec_driver_sql("BEGIN")

        return engine

    def _new_postgres_engine(self: "One", schema_name: str | None = None) -> sa.Engine:
        """
        Open the shared PostgreSQL instance, optionally scoped to one schema.

        When ``schema_name`` is given, every transaction on this engine begins
        by pinning ``search_path`` to it. That is what lets the agent write
        ``SELECT ... FROM loan`` and have it resolve without ever naming the
        schema, which is what keeps one system prompt honest.

        Args:
            schema_name: The schema to pin. ``None`` leaves the server default,
                which is what the sync needs while it is creating that schema.

        Returns:
            An engine, scoped to the schema when one was given.
        """
        url = sa.URL.create(
            drivername="postgresql+psycopg2",
            username=self.config.db_user,
            password=self.config.db_pass,
            host=self.config.db_host,
            port=self.config.db_port,
            database=self.config.db_name,
        )
        engine = sa.create_engine(url)

        if schema_name:
            # Three ways to pin `search_path`, and only the third one holds.
            #
            # The libpq start-up option (`options=-csearch_path=...`) is the
            # obvious one. A pooled endpoint rejects the *connection*, not the
            # query: Neon's `-pooler` host, and PgBouncer generally, answer with
            # "unsupported startup parameter in options: search_path". It fails
            # inside the driver before anything runs, so it surfaces as the app
            # being unable to reach the database at all.
            #
            # A plain `SET search_path` on the `connect` event is what people try
            # next. It appears to work and is not safe: under transaction pooling
            # the proxy hands out a server connection per *transaction*, so the
            # connection the SET ran on need not be the one a later query gets.
            # That failure looks like a table that exists going missing on load.
            #
            # `SET LOCAL` inside the transaction survives both, because the
            # transaction is the unit the proxy already keeps on one server
            # connection. SQLAlchemy opens one implicitly on first execute, so
            # schema reflection and the agent's SQL tool both get it for free.
            quoted_schema = schema_name.replace('"', '""')

            @sa.event.listens_for(engine, "begin")
            def _pin_search_path(connection):
                connection.exec_driver_sql(
                    f'SET LOCAL search_path TO "{quoted_schema}"'
                )

        return engine

    @cached_property
    def remote_postgres_engine(self: "One") -> sa.Engine:
        """
        The shared PostgreSQL instance, unscoped.

        For work that has to reach across schemas -- creating this project's
        schema, inspecting what exists. The agent never uses this one.
        """
        return self._new_postgres_engine()

    @cached_property
    def engine(self: "One") -> sa.Engine:
        """
        The engine everything is served from: our schema in the shared database.

        **The same database in every environment, laptop included.** This used
        to follow the runtime -- SQLite locally, PostgreSQL on Vercel -- which
        meant one agent and two dialects. Every SQL example in the system prompt
        was written and tested against SQLite and then shipped to a PostgreSQL
        deployment, where ``JULIANDAY``, ``strftime`` and ``DATE(x, '-30 days')``
        do not exist. The prompt was correct where nobody was watching and wrong
        in production, and nothing failed loudly: the agent's SQL tool turns a
        database error into a string and hands it back to the model, so the
        symptom was worse answers rather than a crash.

        One database everywhere is what makes a single prompt honest. The cost
        is that local development now needs the ``DB_*`` variables and a
        completed ``scripts/test_06_sync_data_to_remote_db.py``, which is a
        setup step rather than a silent wrong answer.

        SQLite has not gone away: it is still the source of truth that the
        dataset ships and that the sync reads, exposed as
        :attr:`local_sqlite_engine`.
        """
        return self._new_postgres_engine(schema_name=project_config.schema_name)

    @cached_property
    def database_schema_str(self: "One") -> str:
        """
        The database schema, encoded in the LLM-optimized compact format.

        Reflection is scoped to this project's schema, so the agent never sees
        -- and therefore never queries -- another project's tables in the shared
        instance.

        A schema that was never synced reflects successfully and returns
        nothing: an absent schema and an empty one look identical to the
        reflector. The agent would then start with no tables, invent plausible
        ones, and answer confidently out of thin air. Since PostgreSQL became
        the only source, an unsynced database is the likely first-run state, so
        it is named here rather than discovered three wrong answers later.
        """
        # The schema goes on the MetaData, not only on reflect(): the encoder
        # labels the block with `metadata.schema`, and without it the agent is
        # told it is looking at a schema called "default".
        metadata = sa.MetaData(schema=project_config.schema_name)
        metadata.reflect(bind=self.engine, schema=project_config.schema_name)
        schema_info = new_schema_info(
            engine=self.engine,
            metadata=metadata,
            schema_name=project_config.schema_name,
        )
        database_info = new_database_info(
            name=project_config.database_display_name,
            db_type=DbTypeEnum.POSTGRESQL,
            schemas=[
                schema_info,
            ],
        )
        encoded = encode_database_info(database_info=database_info)

        expected = project_config.table_insert_order
        missing = [t for t in expected if t not in encoded]
        if missing:
            raise RuntimeError(
                f"PostgreSQL schema {project_config.schema_name!r} is missing "
                f"{len(missing)} of {len(expected)} table(s): "
                f"{', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}. "
                f"Run `.venv/bin/python scripts/test_06_sync_data_to_remote_db.py` "
                f"to publish the SQLite seed into it."
            )
        return encoded

    def execute_and_print_result(self: "One", sql: str) -> str:
        """Execute a SELECT query and return results as a Markdown table."""
        return execute_and_print_result(
            engine=self.engine,
            sql=sql,
        )
