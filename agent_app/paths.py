# -*- coding: utf-8 -*-

"""
Every path this package needs, in one place.

Paths are facts about the source tree, not configuration: a dataset swap rewrites
the *contents* of ``data/``, never the filenames. So nothing here is routed
through ``data/dataset.toml`` or ``.env`` -- doing that once bought nothing and
forced a circular import between this module and ``project_config``.

Add a path here first, then refer to it as ``path_enum.your_new_path`` everywhere
else. Do not add one speculatively: an entry with no reader silently rots into a
pointer at a directory that no longer exists.
"""

from pathlib import Path
from functools import cached_property


class PathEnum:
    dir_package = Path(__file__).absolute().parent
    dir_project_root = dir_package.parent

    # Coverage report, written by agent_app.tests.helper.
    dir_htmlcov = dir_project_root / "htmlcov"

    # Everything a dataset swap rewrites, in one directory.
    #
    # A swap replaces the contents of ``data/`` and nothing else: the config
    # Python reads, the copy the frontend reads, the explainer, the system
    # prompt, and the database seed. Keeping them together is what makes a swap
    # a directory replacement rather than a diff scattered across the repo, and
    # it is why ``agent_app/`` never has to be touched for one.
    #
    # Not to be confused with ``agent_app/config/``, which holds secrets from
    # ``.env`` and varies per machine rather than per dataset.
    dir_data = dir_project_root / "data"
    path_dataset_toml = dir_data / "dataset.toml"

    # Read by the frontend, never parsed here. Named so that the preflight
    # check can verify they exist without importing TypeScript.
    path_site_toml = dir_data / "site.toml"
    path_business_context_md = dir_data / "business-context.md"

    # The agent's domain brain.
    path_bi_agent_system_prompt_md = dir_data / "system-prompt.md"

    dir_tmp = dir_project_root / "tmp"

    # Written by the agent's ``write_debug_report`` tool.
    path_debug_report_md = dir_tmp / "debug_report.md"

    # Local SQLite database, synced by ``agent_app.tests.db_helper``.
    #
    #   data/data.sqlite.example  (committed to Git, pristine seed)
    #       --copy/overwrite-->
    #   tmp/data.sqlite           (gitignored via the `tmp` rule, working copy)
    #
    # Never commit the working copy: tests and write tools mutate it.
    path_sqlite_db_example = dir_data / "data.sqlite.example"
    path_sqlite_db = dir_tmp / "data.sqlite"

    @cached_property
    def path_bi_agent_system_prompt_content(self) -> str:
        """Read once per process; the prompt is re-read on every agent build."""
        return self.path_bi_agent_system_prompt_md.read_text(encoding="utf-8")


path_enum = PathEnum()
