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
        """A bare Config() fills in the selected provider's default model."""
        config = Config()
        assert config.llm_provider == "bedrock"
        assert config.model_id  # filled in by __post_init__

    def test_unknown_provider(self):
        """An unsupported LLM_PROVIDER fails loudly instead of silently."""
        with pytest.raises(ValueError):
            Config(llm_provider="llama")

    def test_project_name(self):
        """project_name normalizes into snake, slug, and table-prefix forms."""
        config = Config(project_name="SMB Lending-Lens")
        assert config.project_name_snake == "smb_lending_lens"
        assert config.project_name_slug == "smb-lending-lens"
        assert config.prefix_table_name("loan") == "smb_lending_lens_loan"

    def test_llm_api_key(self):
        """llm_api_key returns the selected provider's key; bedrock has none."""
        assert Config(llm_provider="anthropic", anthropic_api_key="k").llm_api_key == "k"
        assert Config(llm_provider="openai", openai_api_key="k").llm_api_key == "k"
        assert Config(llm_provider="google", google_api_key="k").llm_api_key == "k"
        assert Config().llm_api_key is None

    def test_validate(self):
        """validate() checks only the selected provider's credential."""
        Config(aws_region="us-east-1").validate()  # bedrock needs a region
        Config(llm_provider="openai", openai_api_key="k").validate()
        with pytest.raises(ValueError):
            Config().validate()  # bedrock, no region
        with pytest.raises(ValueError):
            Config(llm_provider="openai").validate()  # no key

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
