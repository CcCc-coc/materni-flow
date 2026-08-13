# -*- coding: utf-8 -*-

from pathlib import Path

from learn_smb_lending_lens.sql_utils import execute_and_print_result
from learn_smb_lending_lens.one.api import one

dir_here = Path(__file__).absolute().parent
path_sql = dir_here / "test_02_run_sql_locally.sql"
sql = path_sql.read_text()
execute_and_print_result(engine=one.local_sqlite_engine, sql=sql)
