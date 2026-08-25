# -*- coding: utf-8 -*-

"""
Constant variables used in this project.
"""

import os

from enum_mate.api import BetterStrEnum
from pydantic import BaseModel, Field

TAB = " " * 2


# [startllmproviderenum]
class LlmProviderEnum(BetterStrEnum):
    """
    Supported LLM backends for the BI agent.

    Selected at runtime by the ``LLM_PROVIDER`` environment variable. Exactly one
    provider is active per process; each one needs its own credential (see
    ``.env.example``).
    """

    BEDROCK = "bedrock"  # AWS Bedrock, authenticated with AWS credentials
    ANTHROPIC = "anthropic"  # Claude API, needs ANTHROPIC_API_KEY
    OPENAI = "openai"  # OpenAI API, needs OPENAI_API_KEY
    GOOGLE = "google"  # Gemini API, needs GOOGLE_API_KEY


#: Model used when ``LLM_MODEL_ID`` is not set. One default per provider, since
#: model ID formats are provider specific and not interchangeable.
#:
#: .. warning::
#:
#:     **These IDs go stale.** Vendors release new models, rename them, and retire
#:     old ones on their own schedules, so this mapping is a snapshot of what was
#:     current and cheap when it was written — not a permanent fact. Expect to
#:     revisit it. If a request fails with an "unknown model" / "model not found"
#:     error, check the provider's current model list before debugging anything
#:     else, and override per-environment with ``LLM_MODEL_ID`` in ``.env`` rather
#:     than editing this dict for a one-off.
#:
#: ``openai`` is the default provider (see ``Config.llm_provider``): it needs one
#: API key and no cloud account, which is the lowest barrier for someone opening
#: this repo for the first time.
DEFAULT_MODEL_ID = {
    # Nova Lite: cheap, fast, and good enough for the SQL-and-summarize work this
    # agent does. Step up to us.amazon.nova-pro-v1:0 if answer quality is the issue.
    LlmProviderEnum.BEDROCK.value: "us.amazon.nova-lite-v1:0",
    LlmProviderEnum.ANTHROPIC.value: "claude-haiku-4-5-20251001",
    LlmProviderEnum.OPENAI.value: "gpt-5.6-luna",
    LlmProviderEnum.GOOGLE.value: "gemini-3.5-flash-lite",
}
# [endllmproviderenum]


class LLMColumnConstraintEnum(BetterStrEnum):
    """
    Simplified database column constraints optimized for LLM token efficiency.
    Used in schema encoding to reduce token usage while preserving essential constraint information.
    """

    # relational database
    PK = "PK"  # Primary Key
    UQ = "UQ"  # Unique Key
    IDX = "IDX"  # Index
    FK = "FK"  # Foreign Key
    NN = "NN"  # Not Null
    # aws redshift
    DK = "DK"  # Distribution Key
    SK = "SK"  # Sort Key


class LLMTypeEnum(BetterStrEnum):
    """
    Simplified database column data types optimized for LLM token efficiency.
    Used in schema encoding to represent SQL data types with minimal tokens while preserving semantic meaning.
    """

    STR = "str"  # String/text data of any length
    INT = "int"  # Whole numbers without decimal points
    FLOAT = "float"  # Approximate decimal numbers (IEEE floating point)
    DEC = "dec"  # Exact decimal numbers for currency/financial data
    DT = "dt"  # Date and time combined (local timezone)
    TS = "ts"  # Timestamp with timezone information (UTC)
    DATE = "date"  # Date only without time component
    TIME = "time"  # Time only without date component
    BLOB = "blob"  # Large binary files (images, documents)
    BIN = "bin"  # Small fixed-length binary data (hashes, UUIDs)
    BOOL = "bool"  # True/false boolean values
    NULL = "null"  # Null Type, represents no value


class ObjectTypeEnum(BetterStrEnum):
    """
    Database object types for categorizing different database entities.
    Used in schema introspection and metadata processing to identify object types.
    """

    FOREIGN_KEY = "foreign key"
    COLUMN = "column"
    TABLE = "table"
    VIEW = "view"
    MATERIALIZED_VIEW = "materialized view"
    SCHEMA = "schema"
    DATABASE = "database"

    @property
    def table_type(self) -> "TableTypeEnum":
        return db_object_type_to_table_type_mapping[self]


# [startdbtypeenum]
class DbTypeEnum(BetterStrEnum):
    """
    Supported database system types for connection configuration.
    Used in configuration validation and connection factory selection.
    """

    SQLITE = "sqlite"  # SQLite local databases
    POSTGRESQL = "postgresql"  # PostgreSQL databases
    MYSQL = "mysql"  # MySQL/MariaDB databases
    MSSQL = "mssql"  # Microsoft SQL Server
    ORACLE = "oracle"  # Oracle databases
    AWS_REDSHIFT = "aws_redshift"  # Amazon Redshift data warehouses
    SNOWFLAKE = "snowflake"  # Snowflake cloud databases
    MONGODB = "mongodb"  # MongoDB with SQL interface
    ELASTICSEARCH = "elasticsearch"  # Elasticsearch with SQL
    OPENSEARCH = "opensearch"  # OpenSearch with SQL


# [enddbtypeenum]


class TableTypeEnum(BetterStrEnum):
    """
    Database table types for distinguishing between tables, views, and materialized views.
    Used in schema introspection and metadata categorization for proper object identification.
    """

    TABLE = "Table"
    VIEW = "View"
    MATERIALIZED_VIEW = "MaterializedView"


db_object_type_to_table_type_mapping = {
    ObjectTypeEnum.TABLE: TableTypeEnum.TABLE,
    ObjectTypeEnum.VIEW: TableTypeEnum.VIEW,
    ObjectTypeEnum.MATERIALIZED_VIEW: TableTypeEnum.MATERIALIZED_VIEW,
}


# [startconnectiontypeenum]
class ConnectionTypeEnum(BetterStrEnum):
    """
    Connection types for database connections.
    Used in database :class:`~mcp_ohmy_sql.config.conn.BaseConnection`
    management to differentiate between different connection methods.
    """

    SQLALCHEMY = "sqlalchemy"  # SQLAlchemy connections
    SNOWFLAKE = "snowflake"  # Snowflake
    AWS_REDSHIFT = "aws_redshift"  # AWS Redshift


# [endconnectiontypeenum]


class EnvVar(BaseModel):
    """
    Environment variable wrapper with default value support.
    Used for accessing environment variables throughout the application with fallback defaults.
    """

    name: str = Field()
    default: str = Field(default="")

    @property
    def value(self) -> str:
        return os.environ.get(self.name, self.default)


class EnvVarEnum:
    """
    Collection of predefined environment variables used throughout the application.
    Used for centralized environment variable management and configuration loading.
    """

    MCP_OHMY_SQL_CONFIG = EnvVar(name="MCP_OHMY_SQL_CONFIG")
