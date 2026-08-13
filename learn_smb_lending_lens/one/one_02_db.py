# -*- coding: utf-8 -*-

"""Database mixin for the One class."""

import typing as T
from functools import cached_property

import sqlalchemy as sa

from ..paths import path_enum
from ..runtime import runtime
from ..constants import DbTypeEnum
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
        """Create a SQLite engine connected to the local database file."""
        return sa.create_engine(f"sqlite:///{path_enum.path_sqlite_db}")

    @cached_property
    def remote_postgres_engine(self: "One") -> sa.Engine:
        """Create a PostgreSQL engine connected to the remote database."""
        url = sa.URL.create(
            drivername="postgresql+psycopg2",
            username=self.config.db_user,
            password=self.config.db_pass,
            host=self.config.db_host,
            port=self.config.db_port,
            database=self.config.db_name,
        )
        return sa.create_engine(url)

    @cached_property
    def engine(self: "One") -> sa.Engine:
        """Get the SQLAlchemy engine for database operations."""
        if runtime.is_local():
            return self.local_sqlite_engine
            # return self.remote_postgres_engine
        elif runtime.is_vercel():
            return self.remote_postgres_engine
        else:
            raise NotImplementedError(
                "Only local SQLite engine is implemented in this mixin."
            )

    @cached_property
    def database_schema_str(self: "One") -> str:
        """
        Get the database schema encoded in LLM-optimized compact format.

        Local SQLite holds only this project's tables, so everything is reflected.
        The remote PostgreSQL instance is shared with other projects, so only
        tables carrying this project's prefix are reflected — otherwise the
        agent's schema tool would describe, and happily write queries against,
        tables this project does not own.
        """
        metadata = sa.MetaData()
        if runtime.is_local():
            metadata.reflect(bind=self.engine)
            db_type = DbTypeEnum.SQLITE
        else:
            table_prefix = f"{self.config.project_name_snake}_"
            metadata.reflect(
                bind=self.engine,
                only=lambda table_name, _meta: table_name.startswith(table_prefix),
            )
            db_type = DbTypeEnum.POSTGRESQL
        schema_info = new_schema_info(
            engine=self.engine,
            metadata=metadata,
            schema_name=None,
        )
        database_info = new_database_info(
            name="fintech_smb_lending_pipeline_medium_data",
            db_type=db_type,
            schemas=[
                schema_info,
            ],
        )
        database_info_str = encode_database_info(database_info=database_info)
        return database_info_str

    def execute_and_print_result(self: "One", sql: str) -> str:
        """Execute a SELECT query and return results as a Markdown table."""
        return execute_and_print_result(
            engine=self.engine,
            sql=sql,
        )
