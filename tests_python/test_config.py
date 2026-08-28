# -*- coding: utf-8 -*-

"""
Test for Config.

Signature-level only: build a Config, touch every property and method, and check
the shape of what comes back. No environment mutation, no network, no I/O.
"""

import pytest

from agent_app.config import SCHEMA_NAME_PATTERN, Config
from agent_app.runtime import runtime


class TestConfig:
    def test_defaults(self):
        """A bare Config() fills in the selected provider's default model.

        The default is ``openai`` rather than ``bedrock`` on purpose: it needs
        one API key and no cloud account, which is the lowest barrier for
        someone opening this repo for the first time.
        """
        config = Config()
        assert config.llm_provider == "openai"
        assert config.model_id  # filled in by __post_init__

    def test_unknown_provider(self):
        """An unsupported LLM_PROVIDER fails loudly instead of silently."""
        with pytest.raises(ValueError):
            Config(llm_provider="llama")

    def test_llm_api_key(self):
        """llm_api_key returns the selected provider's key; bedrock has none."""
        assert Config(llm_provider="anthropic", anthropic_api_key="k").llm_api_key == "k"
        assert Config(llm_provider="openai", openai_api_key="k").llm_api_key == "k"
        assert Config(llm_provider="google", google_api_key="k").llm_api_key == "k"
        assert Config(llm_provider="bedrock").llm_api_key is None

    def test_validate(self):
        """validate() checks only the selected provider's credential."""
        Config(openai_api_key="k").validate()  # the default provider
        Config(llm_provider="bedrock", aws_region="us-east-1").validate()
        with pytest.raises(ValueError):
            Config().validate()  # openai, no key
        with pytest.raises(ValueError):
            Config(llm_provider="bedrock").validate()  # no region

    def test_factories(self):
        """Each factory returns a usable Config."""
        assert isinstance(Config.new_in_local_runtime(), Config)
        assert isinstance(Config.new_in_vercel_runtime(), Config)
        assert isinstance(Config.new(), Config)


class TestQuotaConfig:
    def test_cap_on_without_a_table_is_refused(self):
        """
        Caught at start-up rather than on some user's first request. The check
        used to live in ``quota._table``, where a misconfigured public
        deployment booted fine and failed the moment someone typed.
        """
        with pytest.raises(ValueError, match="DYNAMODB_TABLE_NAME_QUOTA"):
            Config(quota_enabled=True)

    def test_cap_on_with_a_table_is_fine(self):
        assert Config(
            quota_enabled=True, dynamodb_table_name_quota="my-quota"
        ).quota_enabled is True

    def test_cap_off_needs_no_table(self):
        assert Config().quota_enabled is False


class TestFactories:
    """
    Two runtimes, one shared reader, exactly one difference between them.

    ``new_from_env_var`` does the reading; the factories differ only in whether
    they hand it AWS credentials. These tests pin that difference, because it is
    the entire reason there are two factories rather than one.
    """

    def test_new_from_env_var_reads_the_environment(self, monkeypatch):
        monkeypatch.setenv("SCHEMA_NAME", "acme_widgets")
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("DB_PORT", "5433")
        monkeypatch.setenv("QUOTA_ENABLED", "true")
        monkeypatch.setenv("DYNAMODB_TABLE_NAME_QUOTA", "my-quota")
        config = Config.new_from_env_var()
        assert config.schema_name == "acme_widgets"
        assert config.llm_provider == "openai"
        assert config.db_port == 5433
        assert config.quota_enabled is True

    def test_new_from_env_var_never_reads_aws_credentials(self, monkeypatch):
        """
        The trap this guards: boto3 checks the environment BEFORE
        ~/.aws/credentials, so a placeholder picked up here would shadow a
        working local profile and Bedrock would fail with an opaque
        UnrecognizedClientException.
        """
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAPLACEHOLDER")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "shhh")
        config = Config.new_from_env_var()
        assert config.aws_access_key_id is None
        assert config.aws_secret_access_key is None

    def test_overrides_win_over_the_environment(self, monkeypatch):
        """How a runtime states its one difference, instead of copying the lot."""
        monkeypatch.setenv("SCHEMA_NAME", "from_env")
        assert Config.new_from_env_var(schema_name="acme_override").schema_name == (
            "acme_override"
        )

    def test_local_leaves_aws_to_the_credential_chain(self, monkeypatch):
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAPLACEHOLDER")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "shhh")
        config = Config.new_in_local_runtime()
        assert config.aws_access_key_id is None
        assert config.aws_secret_access_key is None

    def test_vercel_takes_aws_from_the_environment(self, monkeypatch):
        """Serverless has no ~/.aws, so there is no chain to fall back to."""
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAREAL")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "real")
        config = Config.new_in_vercel_runtime()
        assert config.aws_access_key_id == "AKIAREAL"
        assert config.aws_secret_access_key == "real"

    def test_new_dispatches_to_the_vercel_factory(self, monkeypatch):
        """
        `new()` exists only to pick a factory, and picking the Vercel one is the
        half that never happens on a laptop. Forcing it here is what stops a
        broken dispatch from shipping green.

        `runtime` caches its answer, so the cache has to be dropped on the way
        in and on the way out -- a stale True would leak into every later test.
        """
        runtime.__dict__.pop("_is_vercel", None)
        try:
            monkeypatch.setenv("VERCEL", "1")
            monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAREAL")
            monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "real")
            assert runtime.is_vercel()
            # Reading AWS from the environment is what only the Vercel factory
            # does, so it is the proof of which branch ran.
            assert Config.new().aws_access_key_id == "AKIAREAL"
        finally:
            runtime.__dict__.pop("_is_vercel", None)

    def test_new_dispatches_to_the_local_factory(self, monkeypatch):
        runtime.__dict__.pop("_is_vercel", None)
        try:
            monkeypatch.delenv("VERCEL", raising=False)
            monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAPLACEHOLDER")
            assert runtime.is_local()
            assert Config.new().aws_access_key_id is None
        finally:
            runtime.__dict__.pop("_is_vercel", None)

    def test_placeholder_reads_as_unset(self, monkeypatch):
        """A .env copied from .env.example with "..." left in must not count."""
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "...")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "...")
        config = Config.new_in_vercel_runtime()
        assert config.aws_access_key_id is None
        assert config.aws_secret_access_key is None


class TestSchemaName:
    """
    The dataset's only identifier, from SCHEMA_NAME in the committed
    ``.env.defaults``.

    Checked at construction rather than at first use: the alternative failure is
    a query error from deep inside PostgreSQL, several layers from the typo. The
    value is also interpolated into a ``SET LOCAL search_path`` statement in
    ``one/one_02_db.py``, so it had better be an identifier.
    """

    @pytest.mark.parametrize("ok", ["a", "_private", "acme_widgets", "acme_2", "a" * 63])
    def test_legal_names_are_accepted(self, ok):
        assert Config(schema_name=ok).schema_name == ok
        assert SCHEMA_NAME_PATTERN.fullmatch(ok)

    @pytest.mark.parametrize(
        "bad",
        [
            "My-Schema",  # uppercase and a hyphen
            "acme widgets",  # whitespace
            "2acme",  # leading digit
            "acme;DROP",  # punctuation with no business in an identifier
            "a" * 64,  # one over PostgreSQL's limit
        ],
    )
    def test_illegal_names_are_rejected(self, bad):
        with pytest.raises(ValueError, match="SCHEMA_NAME"):
            Config(schema_name=bad)

    def test_unset_is_allowed_at_construction(self):
        """
        A bare ``Config()`` in a test must not have to know about the dataset.
        An empty schema name fails later, at reflection, with its own message.
        """
        assert Config().schema_name == ""

    def test_committed_default_is_loaded(self):
        """
        The real .env.defaults reaches Config. This is the one test that would
        catch the file being renamed, or Vercel's factory forgetting to load it.
        """
        for config in (Config.new_in_local_runtime(), Config.new_in_vercel_runtime()):
            assert SCHEMA_NAME_PATTERN.fullmatch(config.schema_name)


if __name__ == "__main__":
    from agent_app.tests import run_cov_test

    run_cov_test(
        __file__,
        "agent_app.config",
        preview=False,
    )
