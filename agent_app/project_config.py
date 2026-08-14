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

The dividing line is sharp, and worth stating as a rule: **nothing in this
module varies by environment.** Local, Vercel, and CI all read the same values,
because they all serve the same dataset. Anything that could legitimately differ
between two deployments belongs in :mod:`agent_app.config` instead. If you find
yourself wanting an environment variable to override something here, the value
is in the wrong module.

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

    project_config.project_name          # "smbll"
    project_config.project_name_snake    # "smbll"
    project_config.prefix_table_name("loan")  # "smbll_loan"
    project_config.table_insert_order    # ["industry", "risk_grade", ...]
"""

import re
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

        This is what namespaces tables in the shared remote database. It lives
        here rather than in ``.env`` because it is not a secret and not
        machine-specific: every deployment of *this* dataset wants the same
        value, so committing it removes one more thing to forget on a swap.

        Keep it short: it is prefixed onto every remote table name, and
        PostgreSQL identifiers cap at 63 characters.
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
    def project_name_snake(self) -> str:
        """
        The project name as a snake_case identifier, e.g. ``smb_lending_lens``.

        Use this wherever the name has to be a valid SQL / Python identifier —
        most importantly as the prefix on remote database table names, which is
        how several projects share one NeonDB instance without colliding.

        Any run of characters that is not a letter or digit collapses to a single
        underscore, so ``"SMB Lending-Lens"`` and ``"smb_lending_lens"`` normalize
        to the same value.
        """
        return re.sub(r"[^a-z0-9]+", "_", self.project_name.strip().lower()).strip("_")

    @property
    def project_name_slug(self) -> str:
        """
        The project name as a hyphenated slug, e.g. ``smb-lending-lens``.

        Same normalization as :attr:`project_name_snake`, but with hyphens — the
        form wanted by things that live in a URL or a hostname (deployment names,
        S3 buckets, DNS labels), where underscores are awkward or illegal.
        """
        return re.sub(r"[^a-z0-9]+", "-", self.project_name.strip().lower()).strip("-")

    def prefix_table_name(self, table_name: str) -> str:
        """
        Namespace a table name for the shared remote database.

        Args:
            table_name: The local, unprefixed table name, e.g. ``"loan"``.

        Returns:
            The remote table name, e.g. ``"smbll_loan"``.
        """
        return f"{self.project_name_snake}_{table_name}"


project_config = ProjectConfig()
