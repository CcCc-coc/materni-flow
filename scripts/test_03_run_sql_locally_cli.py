# -*- coding: utf-8 -*-

import fire
from agent_app.sql_utils import execute_sql_query
from agent_app.one.api import one


def main(sql: str):
    print(execute_sql_query(engine=one.local_sqlite_engine, sql=sql))


if __name__ == "__main__":
    fire.Fire(main)
