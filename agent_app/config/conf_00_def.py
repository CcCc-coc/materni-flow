# -*- coding: utf-8 -*-

"""
Centralized Configuration Management
====================================

This module implements the **Config Pattern** — a common approach for managing
application configuration across different runtime environments.

Why this pattern?
-----------------

Applications need different configurations in different environments:

- **Local development:** Use ``~/.aws/credentials``, connect to dev databases
- **Vercel/Cloud:** Read secrets from environment variables, connect to prod services

The naive approach scatters ``if runtime.is_vercel()`` checks throughout the codebase.
This leads to:

- Duplicated logic in multiple files
- Hard to track what configuration differs between environments
- Easy to miss a check and introduce bugs

The Config Pattern solves this by **centralizing all environment-specific logic
in one place**.

What does NOT belong here
-------------------------

Anything that is the same in every environment. The project's name, the tables
it owns, and the database it describes are properties of the *dataset*, not of
the machine, so they live in :mod:`agent_app.project_config` and are read from
``data/dataset.toml``. Duplicating such a value here, even with an environment
variable as an escape hatch, gives it two homes and eventually two answers.

How it works
------------

1. **Define a Config dataclass** with all configurable values as fields
2. **Create factory methods** for each runtime environment (``new_in_local_runtime``,
   ``new_in_vercel_runtime``)
3. **Expose a singleton** ``config`` instance at module level
4. **Import and use** ``config.xxx`` anywhere in the codebase

Example usage::

    from agent_app.config import config

    # Anywhere in your code - no environment checks needed
    session = boto3.Session(
        region_name=config.aws_region,
        aws_access_key_id=config.aws_access_key_id,
        aws_secret_access_key=config.aws_secret_access_key,
    )

Benefits
--------

- **One place complex, everywhere else simple** — Environment detection happens
  once in ``Config.new()``. All other code just reads ``config.xxx``.
- **Easy to extend** — Need a new config value? Add a field and set it in the
  factory methods. All existing code continues to work.
- **Testable** — Tests can create ``Config`` instances directly with test values,
  bypassing the runtime detection entirely.
- **Self-documenting** — The dataclass fields serve as documentation of what
  can be configured.

Adding new configuration
------------------------

To add a new configurable value:

1. Add a field to the ``Config`` dataclass
2. Set appropriate values in ``new_in_local_runtime()`` and ``new_in_vercel_runtime()``
3. Use ``config.your_new_field`` anywhere in the codebase

That's it. No need to add ``if runtime.is_xxx()`` checks anywhere else.

Choosing an LLM provider
------------------------

The agent talks to exactly one LLM backend per process, chosen by the
``LLM_PROVIDER`` environment variable (``bedrock`` by default). Each provider
authenticates differently, so only the credential belonging to the *selected*
provider is required — the others may be absent::

    LLM_PROVIDER=bedrock     -> AWS credentials (env vars, or ~/.aws/credentials)
    LLM_PROVIDER=anthropic   -> ANTHROPIC_API_KEY
    LLM_PROVIDER=openai      -> OPENAI_API_KEY
    LLM_PROVIDER=google      -> GOOGLE_API_KEY

Call :meth:`Config.validate` to fail fast with a readable message when the
selected provider's credential is missing.
"""

import os
import dataclasses

from ..runtime import runtime
from ..constants import LlmProviderEnum, DEFAULT_MODEL_ID


#: The placeholder ``.env.example`` uses for values the reader has to fill in.
PLACEHOLDER = "..."


def get_env(name: str) -> str | None:  # pragma: no cover
    """
    Read an environment variable, treating the ``"..."`` placeholder as unset.

    ``load_dotenv()`` has no notion of a placeholder: a ``.env`` copied from
    ``.env.example`` with ``AWS_ACCESS_KEY_ID="..."`` left uncommented gives you
    a variable that is set, non-empty, and useless. boto3 reads env vars before
    ``~/.aws/credentials``, so that placeholder shadows a working local profile
    and Bedrock fails with ``UnrecognizedClientException``. Returning None lets
    each SDK fall back to its own credential chain.

    Returns:
        The value, or None if unset or still the placeholder.
    """
    value = os.environ.get(name)
    if value == PLACEHOLDER:
        return None
    return value


def get_env_bool(name: str, default: bool = False) -> bool:  # pragma: no cover
    """
    Read an environment variable as a boolean.

    Accepts the spellings people actually type in a ``.env``: ``1/0``,
    ``true/false``, ``yes/no``, ``on/off``, any case. Anything else falls back to
    ``default`` rather than raising, because a malformed flag should not stop the
    app from booting -- it should just leave the feature in its default state.

    Returns:
        The parsed boolean, or ``default`` if unset or unrecognized.
    """
    value = get_env(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def get_env_int(name: str) -> int | None:  # pragma: no cover
    """
    Read an environment variable as an int, or None if unset / not a number.

    Env vars are always strings, so something has to do the conversion. Doing it
    here means a blank or malformed ``DB_PORT`` yields None, which callers
    already treat as "not configured", instead of a ValueError at import time.

    Returns:
        The parsed integer, or None if unset or not a valid integer.
    """
    value = get_env(name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


#: Environment variable holding the credential for each API-key based provider.
#: Bedrock is absent on purpose: it authenticates with AWS credentials, not a key.
PROVIDER_API_KEY_ENV_VAR = {
    LlmProviderEnum.ANTHROPIC.value: "ANTHROPIC_API_KEY",
    LlmProviderEnum.OPENAI.value: "OPENAI_API_KEY",
    LlmProviderEnum.GOOGLE.value: "GOOGLE_API_KEY",
}


@dataclasses.dataclass
class Config:
    """
    Application configuration container.

    This dataclass holds all environment-specific configuration values.
    Use the factory methods to create instances, or use the module-level
    ``config`` singleton for normal application code.

    Attributes:
        llm_provider: Which LLM backend to talk to. One of :class:`LlmProviderEnum`.
            Defaults to ``openai``, which needs only an ``OPENAI_API_KEY``.
            Bedrock needs an AWS account, and not everyone picking this repo up
            has one.
        model_id: Model identifier for the selected provider. When None, the
            provider's default from ``DEFAULT_MODEL_ID`` is filled in.
        max_tokens: Maximum tokens the model may generate in one response.
            Required by the Anthropic provider, ignored by the others.
        aws_region: AWS region for all AWS services (e.g., "us-east-1")
        aws_access_key_id: AWS access key. None means use default credential chain.
        aws_secret_access_key: AWS secret key. None means use default credential chain.
        anthropic_api_key: Claude API key, used when llm_provider is "anthropic".
        openai_api_key: OpenAI API key, used when llm_provider is "openai".
        google_api_key: Gemini API key, used when llm_provider is "google".
        db_host: PostgreSQL host. Only needed for the remote Postgres engine;
            local development reads the SQLite file instead.
        db_port: PostgreSQL port.
        db_user: PostgreSQL user.
        db_pass: PostgreSQL password.
        db_name: PostgreSQL database name.
        quota_enabled: Whether to meter and cap monthly LLM spend. **Off by
            default**: a student running this locally is spending their own
            Bedrock allowance and needs no cap, and turning it on requires a
            DynamoDB table that does not exist until someone creates it.
        dynamodb_table_name_quota: DynamoDB table holding the counters. Only
            read when ``quota_enabled`` is true.
        quota_max_invoke_per_month: Cap on agent invocations per calendar month.
        quota_max_input_token_per_month: Cap on input tokens per calendar month.
        quota_max_output_token_per_month: Cap on output tokens per calendar month.
    """

    # --- LLM ---
    llm_provider: str = dataclasses.field(default=LlmProviderEnum.OPENAI.value)
    model_id: str | None = dataclasses.field(default=None)
    max_tokens: int = dataclasses.field(default=8192)
    # --- AWS (used by the bedrock provider) ---
    aws_region: str | None = dataclasses.field(default=None)
    aws_access_key_id: str | None = dataclasses.field(default=None)
    aws_secret_access_key: str | None = dataclasses.field(default=None)
    # --- API keys (one per non-bedrock provider) ---
    anthropic_api_key: str | None = dataclasses.field(default=None)
    openai_api_key: str | None = dataclasses.field(default=None)
    google_api_key: str | None = dataclasses.field(default=None)
    # --- Database ---
    db_host: str | None = dataclasses.field(default=None)
    db_port: int | None = dataclasses.field(default=None)
    db_user: str | None = dataclasses.field(default=None)
    db_pass: str | None = dataclasses.field(default=None)
    db_name: str | None = dataclasses.field(default=None)
    # --- Monthly LLM spend cap (see agent_app/quota.py) ---
    quota_enabled: bool = dataclasses.field(default=False)
    dynamodb_table_name_quota: str | None = dataclasses.field(default=None)
    quota_max_invoke_per_month: int = dataclasses.field(default=1000)
    quota_max_input_token_per_month: int = dataclasses.field(default=50_000_000)
    quota_max_output_token_per_month: int = dataclasses.field(default=10_000_000)

    def __post_init__(self):
        """
        Normalize the provider and fill in its default model ID.

        Doing this here (rather than in the factories) means a hand-built
        ``Config()`` in a test behaves exactly like one built from the environment.
        """
        self.llm_provider = (self.llm_provider or "").strip().lower()
        if self.llm_provider not in DEFAULT_MODEL_ID:
            raise ValueError(
                f"Unknown LLM_PROVIDER {self.llm_provider!r}. "
                f"Expected one of: {', '.join(sorted(DEFAULT_MODEL_ID))}."
            )
        if self.model_id is None:
            self.model_id = DEFAULT_MODEL_ID[self.llm_provider]

    @property
    def llm_api_key(self) -> str | None:
        """
        The API key belonging to the selected provider.

        Returns None for ``bedrock``, which uses AWS credentials instead.
        """
        return {
            LlmProviderEnum.ANTHROPIC.value: self.anthropic_api_key,
            LlmProviderEnum.OPENAI.value: self.openai_api_key,
            LlmProviderEnum.GOOGLE.value: self.google_api_key,
        }.get(self.llm_provider)

    def validate(self):
        """
        Fail fast when the selected provider's credential is missing.

        Only the *selected* provider is checked. The other providers' keys may be
        absent, which is the whole point of switching with ``LLM_PROVIDER``.

        Raises:
            ValueError: If the selected provider has no usable credential.
        """
        if self.llm_provider == LlmProviderEnum.BEDROCK.value:
            # boto3 resolves credentials from env vars, ~/.aws/credentials, or an
            # IAM role, so there is nothing to assert here beyond the region.
            if not self.aws_region:
                raise ValueError(
                    "llm_provider is 'bedrock' but aws_region is not set. "
                    "Set AWS_REGION in your .env file."
                )
            return

        env_var = PROVIDER_API_KEY_ENV_VAR[self.llm_provider]
        if not self.llm_api_key:
            raise ValueError(
                f"llm_provider is {self.llm_provider!r} but {env_var} is not set. "
                f"Add {env_var}=... to your .env file, or switch LLM_PROVIDER."
            )

    @classmethod
    def new_in_local_runtime(cls):
        """
        Build config for local development.

        AWS credentials are deliberately NOT read from the environment here: boto3
        checks ``AWS_ACCESS_KEY_ID`` / ``AWS_SECRET_ACCESS_KEY`` before it reads
        ``~/.aws/credentials``, so passing them through would let a placeholder in
        ``.env`` shadow a perfectly good local profile.
        """
        from dotenv import load_dotenv

        load_dotenv()

        return cls(
            llm_provider=get_env("LLM_PROVIDER") or LlmProviderEnum.BEDROCK.value,
            model_id=get_env("LLM_MODEL_ID"),
            aws_region=get_env("AWS_REGION") or "us-east-1",
            anthropic_api_key=get_env("ANTHROPIC_API_KEY"),
            openai_api_key=get_env("OPENAI_API_KEY"),
            google_api_key=get_env("GOOGLE_API_KEY"),
            db_host=get_env("DB_HOST"),
            db_port=get_env_int("DB_PORT"),
            db_user=get_env("DB_USER"),
            db_pass=get_env("DB_PASS"),
            db_name=get_env("DB_NAME"),
            quota_enabled=get_env_bool("QUOTA_ENABLED"),
            dynamodb_table_name_quota=get_env("DYNAMODB_TABLE_NAME_QUOTA"),
            quota_max_invoke_per_month=get_env_int("QUOTA_MAX_INVOKE_PER_MONTH") or 1000,
            quota_max_input_token_per_month=(
                get_env_int("QUOTA_MAX_INPUT_TOKEN_PER_MONTH") or 50_000_000
            ),
            quota_max_output_token_per_month=(
                get_env_int("QUOTA_MAX_OUTPUT_TOKEN_PER_MONTH") or 10_000_000
            ),
        )

    @classmethod
    def new_in_vercel_runtime(cls):
        """
        Build config for Vercel.

        Serverless has no ``~/.aws``, so AWS credentials must come from environment
        variables. The database is always the remote Postgres instance here.
        """
        return cls(
            llm_provider=get_env("LLM_PROVIDER") or LlmProviderEnum.BEDROCK.value,
            model_id=get_env("LLM_MODEL_ID"),
            aws_region=get_env("AWS_REGION") or "us-east-1",
            aws_access_key_id=get_env("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=get_env("AWS_SECRET_ACCESS_KEY"),
            anthropic_api_key=get_env("ANTHROPIC_API_KEY"),
            openai_api_key=get_env("OPENAI_API_KEY"),
            google_api_key=get_env("GOOGLE_API_KEY"),
            db_host=get_env("DB_HOST"),
            db_port=get_env_int("DB_PORT"),
            db_user=get_env("DB_USER"),
            db_pass=get_env("DB_PASS"),
            db_name=get_env("DB_NAME"),
            quota_enabled=get_env_bool("QUOTA_ENABLED"),
            dynamodb_table_name_quota=get_env("DYNAMODB_TABLE_NAME_QUOTA"),
            quota_max_invoke_per_month=get_env_int("QUOTA_MAX_INVOKE_PER_MONTH") or 1000,
            quota_max_input_token_per_month=(
                get_env_int("QUOTA_MAX_INPUT_TOKEN_PER_MONTH") or 50_000_000
            ),
            quota_max_output_token_per_month=(
                get_env_int("QUOTA_MAX_OUTPUT_TOKEN_PER_MONTH") or 10_000_000
            ),
        )

    @classmethod
    def new(cls):
        """
        Factory method that creates the appropriate Config for the current runtime.

        This is the main entry point for creating Config instances. It automatically
        detects the runtime environment and returns a properly configured instance.

        Returns:
            Config: A Config instance configured for the detected runtime.

        Raises:
            RuntimeError: If the runtime environment is not recognized.
        """
        if runtime.is_local():
            return cls.new_in_local_runtime()
        elif runtime.is_vercel():
            return cls.new_in_vercel_runtime()
        else:  # pragma: no cover
            raise RuntimeError
