# -*- coding: utf-8 -*-

import fire
from agent_app.sql_utils import execute_sql_query
from agent_app.dataset import local_sqlite_engine


def main(sql: str):
    print(execute_sql_query(engine=local_sqlite_engine(), sql=sql))


if __name__ == "__main__":
    fire.Fire(main)
