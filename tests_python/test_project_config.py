# -*- coding: utf-8 -*-

"""
Test for ProjectConfig.

Reads the real ``data/dataset.toml``, because the point of this module is that
there is exactly one copy of these values and it is committed. Building one from
a literal would test the dataclass, not the config.
"""

from pathlib import Path

from agent_app.project_config import ProjectConfig, project_config


class TestProjectConfig:
    def test_reads_the_committed_toml(self):
        """The singleton parses data/dataset.toml and finds all three sections."""
        assert project_config.project_name
        assert project_config.database_display_name
        assert len(project_config.table_insert_order) > 0

    def test_table_insert_order_is_a_fresh_list(self):
        """Callers get a copy, so mutating the result cannot corrupt the cache."""
        first = project_config.table_insert_order
        first.append("bogus")
        assert "bogus" not in project_config.table_insert_order

    def test_name_derivations(self, tmp_path: Path):
        """project_name normalizes into snake and slug forms."""
        toml = tmp_path / "dataset.toml"
        toml.write_text(
            '[project]\nname = "SMB Lending-Lens"\n'
            '[database]\nschemaName = "smb_lending"\n'
            'displayName = "d"\ntableInsertOrder = ["loan"]\n',
            encoding="utf-8",
        )
        cfg = ProjectConfig(path_dataset_toml=toml)
        assert cfg.project_name_snake == "smb_lending_lens"
        assert cfg.project_name_slug == "smb-lending-lens"
        # The schema name is read, not derived: it namespaces this project's
        # tables in the shared database and must not silently follow a rebrand.
        assert cfg.schema_name == "smb_lending"

    def test_no_environment_dependence(self, monkeypatch):
        """
        Nothing here reads the environment. PROJECT_NAME used to override the
        name via Config; that duplication is gone, and this test is what keeps
        it gone.
        """
        monkeypatch.setenv("PROJECT_NAME", "should_be_ignored")
        assert project_config.project_name != "should_be_ignored"
