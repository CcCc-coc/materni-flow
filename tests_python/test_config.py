# -*- coding: utf-8 -*-

"""
Test for Config.

Signature-level only: build a Config, touch every property and method, and check
the shape of what comes back. No environment mutation, no network, no I/O.
"""

import pytest

from agent_app.config import SCHEMA_NAME_PATTERN, Config


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
