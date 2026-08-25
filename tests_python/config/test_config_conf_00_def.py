# -*- coding: utf-8 -*-

"""
Test for Config.

Signature-level only: build a Config, touch every property and method, and check
the shape of what comes back. No environment mutation, no network, no I/O.
"""

import pytest

from agent_app.config.conf_00_def import Config


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


if __name__ == "__main__":
    from agent_app.tests import run_cov_test

    run_cov_test(
        __file__,
        "agent_app.config.conf_00_def",
        preview=False,
    )
