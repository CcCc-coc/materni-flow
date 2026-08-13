# -*- coding: utf-8 -*-

"""
Database helper functions for local development and testing.

Sync mechanism
--------------

The local SQLite database is seeded from a pristine copy that **is** committed
to Git::

    data.sqlite.example   (repo root, tracked by Git, never modified)
            |
            |  copy + overwrite
            v
    tmp/data.sqlite       (gitignored, the working copy)

``tmp/data.sqlite`` is what the app and the tests actually read and write, so it
drifts as soon as any write tool runs. Re-running :func:`setup_sqlite_db` throws
that drift away and restores a known-good state.

This replaces the old mechanism, which downloaded the database from a GitHub
Release over the network. Seeding from a tracked file means no network access is
needed and every checkout starts from the exact same data.
"""

import shutil
from pathlib import Path

from ..paths import path_enum


def setup_sqlite_db(
    src: Path = path_enum.path_sqlite_db_example,
    dest: Path = path_enum.path_sqlite_db,
    overwrite: bool = True,
) -> Path:
    """
    Seed the working SQLite database from the committed example file.

    Args:
        src: Pristine seed file tracked by Git (``data.sqlite.example``).
        dest: Working copy used by the app and tests (``tmp/data.sqlite``).
        overwrite: If True (default), always replace an existing working copy.
            If False, keep the existing file and do nothing.

    Returns:
        Path to the working copy.

    Raises:
        FileNotFoundError: If the seed file is missing.
    """
    if src.exists() is False:
        raise FileNotFoundError(
            f"Seed database not found: {src}\n"
            f"This file is tracked by Git — try 'git checkout {src.name}'."
        )

    if dest.exists() and overwrite is False:
        print(f"Database already exists, keeping it: {dest}")
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)

    print(f"Copied {src.name} -> {dest.name}")
    print(f"Database ready at: {dest} ({dest.stat().st_size:,} bytes)")
    return dest


def reset_test_database() -> Path:
    """
    Reset the working database back to the pristine seed.

    Use this to discard any mutation made by write operations, so tests start
    from a clean, known state.

    Returns:
        Path to the freshly seeded working copy.
    """
    return setup_sqlite_db(overwrite=True)
