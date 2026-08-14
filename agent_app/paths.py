# -*- coding: utf-8 -*-

from pathlib import Path
from functools import cached_property


class PathEnum:
    dir_package = Path(__file__).absolute().parent
    dir_project_root = dir_package.parent

    # Virtual Environment
    dir_venv = dir_project_root / ".venv"
    dir_venv_bin = dir_venv / "bin"
    path_venv_bin_pip = dir_venv_bin / "pip"
    path_venv_bin_python = dir_venv_bin / "python"
    path_venv_bin_pytest = dir_venv_bin / "pytest"

    # Test
    dir_htmlcov = dir_project_root / "htmlcov"
    path_cov_index_html = dir_htmlcov / "index.html"
    dir_unit_test = dir_project_root / "tests"
    dir_int_test = dir_project_root / "tests_int"
    dir_load_test = dir_project_root / "tests_load"

    @cached_property
    def dir_home(self) -> Path:
        return Path.home()

    # Dataset configuration, committed to Git, read by Python only. The
    # frontend's half lives in `config/site.ts` and is never parsed here.
    # Not to be confused with `agent_app/config/`, which holds secrets from `.env`.
    dir_config = dir_project_root / "config"
    path_dataset_toml = dir_config / "dataset.toml"

    dir_prompts = dir_package / "prompts"
    path_instruction_md = dir_prompts / "instruction.md"
    path_knowledge_base_md = dir_prompts / "knowledge-base.md"

    # The agent's system prompt. Fixed here rather than named in config: it is
    # part of the source tree, and a dataset swap rewrites its contents, not its
    # filename. Routing it through config bought nothing and forced a circular
    # import between this module and ``project_config``.
    path_bi_agent_system_prompt_md = dir_prompts / "bi-agent-system-prompt.md"

    @cached_property
    def instruction_content(self) -> str:
        return self.path_instruction_md.read_text(encoding="utf-8")

    @cached_property
    def knowledge_base_content(self) -> str:
        return self.path_knowledge_base_md.read_text(encoding="utf-8")

    @cached_property
    def path_bi_agent_system_prompt_content(self) -> str:
        return self.path_bi_agent_system_prompt_md.read_text(encoding="utf-8")

    dir_tmp = dir_project_root / "tmp"

    # Written by the agent's ``write_debug_report`` tool.
    path_debug_report_md = dir_tmp / "debug_report.md"

    # Local SQLite database, synced by ``agent_app.tests.db_helper``.
    #
    #   data.sqlite.example  (repo root, committed to Git, pristine seed)
    #       --copy/overwrite-->
    #   tmp/data.sqlite      (gitignored via the `tmp` rule, the working copy)
    #
    # Never commit the working copy: tests and write tools mutate it.
    path_sqlite_db_example = dir_project_root / "data.sqlite.example"
    path_sqlite_db = dir_tmp / "data.sqlite"


path_enum = PathEnum()
