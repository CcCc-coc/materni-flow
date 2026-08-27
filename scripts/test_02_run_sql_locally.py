# -*- coding: utf-8 -*-

from pathlib import Path

from agent_app.sql_utils import execute_sql_query
from agent_app.one.api import one

dir_here = Path(__file__).absolute().parent
path_sql = dir_here / "test_02_run_sql_locally.sql"
sql = path_sql.read_text()
print(execute_sql_query(engine=one.local_sqlite_engine, sql=sql))
