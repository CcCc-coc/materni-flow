# -*- coding: utf-8 -*-

"""
Dataset configuration: the Python half of the ``config/`` directory.

Two config layers, two jobs
---------------------------

This repo has two things that both get called "config", and they are not the
same thing:

- :mod:`agent_app.config` (``conf_00_def.py``) holds **secrets and
  environment-specific values** — API keys, database credentials, which LLM
  provider to talk to. Those come from ``.env`` and differ per *machine*.

- This module holds **dataset identity** — what the project is called, what
  database it describes, which prompt it loads. Those come from
  ``config/dataset.toml``, are committed to Git, and differ per *dataset*.

The split matters because they change for different reasons. Rotating an API key
should not touch the project's name; pointing the repo at a new dataset should
not touch anyone's credentials.

Why this file is so small
-------------------------

``config/dataset.toml`` holds only what Python actually reads. Everything the UI
says lives in ``config/site.ts`` instead, because it is consumed exclusively by
TypeScript and gets type checking there that JSON could never provide. The two
runtimes were found to read disjoint sets of keys, so a single shared config
file was two unrelated files stapled together.

TOML rather than JSON so the file can carry real comments explaining what each
value is for. ``tomllib`` ships with Python 3.11+, so this costs no dependency.

Example usage::

    from agent_app.project_config import project_config

    project_config.project_name        # "smbll"
    project_config.database_display_name
    project_config.table_insert_order  # ["industry", "risk_grade", ...]
"""

import tomllib
import typing as T
import dataclasses
from pathlib import Path
from functools import cached_property

from .paths import path_enum


@dataclasses.dataclass
class ProjectConfig:
    """
    Typed reader over ``config/dataset.toml``.

    Attributes:
        path_dataset_toml: Location of the dataset config file.
    """

    path_dataset_toml: Path = dataclasses.field(default=path_enum.path_dataset_toml)

    @cached_property
    def dataset(self) -> dict[str, T.Any]:
        """Parsed ``config/dataset.toml``."""
        return tomllib.loads(self.path_dataset_toml.read_text(encoding="utf-8"))

    @property
    def project_name(self) -> str:
        """
        Short identifier for this project, e.g. ``"smbll"``.

        This is what namespaces tables in the shared remote database. It lives in
        ``dataset.toml`` rather than ``.env`` because it is not a secret and not
        machine-specific: every deployment of *this* dataset wants the same
        value, so committing it removes one more thing to forget on a swap.
        ``PROJECT_NAME`` in the environment still wins if it is set, which keeps
        the escape hatch open for a one-off deployment.
        """
        return self.dataset["project"]["name"]

    @property
    def database_display_name(self) -> str:
        """
        The database name shown to the LLM at the top of the encoded schema.

        Purely descriptive — it labels the schema block the agent reads, and does
        not have to match any real database name.
        """
        return self.dataset["database"]["displayName"]

    @property
    def table_insert_order(self) -> list[str]:
        """
        Table names in foreign-key dependency order: parents first.

        Single source of truth for both directions of the remote sync — inserts
        walk it forwards, drops walk it backwards. See
        :mod:`agent_app.tests.db_sync`.
        """
        return list(self.dataset["database"]["tableInsertOrder"])

    @property
    def path_system_prompt(self) -> Path:
        """The agent's system prompt file, as named by ``dataset.toml``."""
        return path_enum.dir_project_root / self.dataset["agent"]["promptFile"]


project_config = ProjectConfig()
