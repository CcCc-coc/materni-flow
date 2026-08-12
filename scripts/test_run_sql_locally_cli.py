# -*- coding: utf-8 -*-

import fire
from learn_smb_lending_lens.sql_utils import execute_and_print_result
from learn_smb_lending_lens.one.api import one


def main(sql: str):
    execute_and_print_result(engine=one.local_sqlite_engine, sql=sql)


if __name__ == "__main__":
    fire.Fire(main)
