# -*- coding: utf-8 -*-

"""
Project configuration: the Python half of the ``config/`` directory.

Two config layers, two jobs
---------------------------

This repo has two things that both get called "config", and they are not the
same thing:

- :mod:`agent_app.config` (``conf_00_def.py``) holds **secrets and
  environment-specific values** — API keys, database credentials, which LLM
  provider to talk to. Those come from ``.env`` and differ per *machine*.

- This module holds **project identity** — what the project is called, what
  database it describes, what the UI says. Those come from
  ``config/dataset.json``, are committed to Git, and differ per *dataset*.

The split matters because they change for different reasons. Rotating an API key
should not touch the project's name; pointing the repo at a new dataset should
not touch anyone's credentials.

Why JSON, read at runtime
-------------------------

``config/dataset.json`` is read directly by *both* runtimes: Next.js imports
it, this module parses it. No code generation, no build step, no chance of the
two halves drifting apart — there is exactly one copy of every string, and both
languages point at it.

Example usage::

    from agent_app.project_config import project_config

    project_config.project_name        # "smbll"
    project_config.database_display_name
    project_config.table_insert_order  # ["industry", "risk_grade", ...]
"""

import json
import typing as T
import dataclasses
from pathlib import Path
from functools import cached_property

from .paths import path_enum


@dataclasses.dataclass
class ProjectConfig:
    """
    Typed reader over ``config/dataset.json``.

    Only the handful of values the Python side actually needs get named
    properties. The rest of the file is UI copy that never reaches Python, so it
    is left in :attr:`dataset` as a plain dict rather than mirrored into fields
    that would have to be kept in sync by hand.

    Attributes:
        path_dataset_json: Location of the dataset config file.
    """

    path_dataset_json: Path = dataclasses.field(default=path_enum.path_dataset_json)

    @cached_property
    def dataset(self) -> dict[str, T.Any]:
        """Parsed ``config/dataset.json``."""
        return json.loads(self.path_dataset_json.read_text(encoding="utf-8"))

    @property
    def project_name(self) -> str:
        """
        Short identifier for this project, e.g. ``"smbll"``.

        This is what namespaces tables in the shared remote database. It lives in
        ``dataset.json`` rather than ``.env`` because it is not a secret and not
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
    def retired_terms(self) -> list[str]:
        """
        Vocabulary from datasets this repo used to serve.

        ``scripts/test_00_check_project_config.py`` fails the build if any of
        these words survive anywhere in the code. See the ``checks`` section of
        ``config/dataset.json``.
        """
        return list(self.dataset.get("checks", {}).get("retiredTerms", []))

    @property
    def path_system_prompt(self) -> Path:
        """The agent's system prompt file, as named by ``dataset.json``."""
        return path_enum.dir_project_root / self.dataset["agent"]["promptFile"]


project_config = ProjectConfig()
