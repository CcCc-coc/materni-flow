# -*- coding: utf-8 -*-

"""
Download SQLite database file from GitHub Release.

Usage:
    python scripts/test_download_sqlite_file.py

The file will be downloaded to: tmp/data.sqlite
"""

from learn_smb_lending_lens.tests.db_helper import download_sqlite_db

if __name__ == "__main__":
    download_sqlite_db()
