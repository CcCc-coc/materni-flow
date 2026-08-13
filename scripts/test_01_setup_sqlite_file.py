# -*- coding: utf-8 -*-

"""
Seed the local SQLite database from the committed example file.

Usage:
    python scripts/test_01_setup_sqlite_file.py

Copies (overwriting) data.sqlite.example -> tmp/data.sqlite.
"""

from learn_smb_lending_lens.tests.db_helper import setup_sqlite_db

if __name__ == "__main__":
    setup_sqlite_db()
