# -*- coding: utf-8 -*-

"""
Enums shared across modules.

Two unrelated families live here, kept together only because this file is a
zero-dependency leaf that everything else may import:

- ``LlmProviderEnum`` / ``DEFAULT_MODEL_ID`` -- read by ``config/`` and
  ``one/one_04_agent.py``.
- The ``LLM*`` / ``ObjectTypeEnum`` / ``TableTypeEnum`` / ``DbTypeEnum`` vocabulary
  -- read by ``db_schema/`` and ``one/one_02_db.py``.

Nothing dataset-specific belongs here. A value that varies per machine goes to
``config/conf_00_def.py``; one that varies per dataset goes to ``data/dataset.toml``.
"""

from enum_mate.api import BetterStrEnum


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


class LLMColumnConstraintEnum(BetterStrEnum):
    """
    Simplified database column constraints optimized for LLM token efficiency.
    Used in schema encoding to reduce token usage while preserving essential constraint information.
    """

    PK = "PK"  # Primary Key
    UQ = "UQ"  # Unique Key
    IDX = "IDX"  # Index
    FK = "FK"  # Foreign Key
    NN = "NN"  # Not Null


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


class TableTypeEnum(BetterStrEnum):
    """
    What kind of table-like object a reflected relation is.

    The only distinction the schema encoder draws, and the values are the labels
    the LLM actually sees -- ``Table Product(...)``, ``View SalesReport(...)``.

    There used to be a second, broader ``ObjectTypeEnum`` (column, schema,
    database, foreign key) alongside this one, plus a dict translating between
    the two. Nothing read the extra members: every model knew its own kind
    statically, so the field only ever held the value its class already implied.
    """

    TABLE = "Table"
    VIEW = "View"
    MATERIALIZED_VIEW = "MaterializedView"


class DbTypeEnum(BetterStrEnum):
    """
    Database engines this scaffold actually runs against.

    Deliberately short. It used to list ten engines copied in from elsewhere, nine
    of which no code path could reach -- a menu of options that were never
    implemented reads as support that does not exist. Add an entry when the code
    path that uses it is added, not before.
    """

    SQLITE = "sqlite"  # local seed and sync source, tmp/data.sqlite
    POSTGRESQL = "postgresql"  # what the agent reads in every environment
