# -*- coding: utf-8 -*-

"""
Run any SELECT against the local SQLite seed and print it as a table.

Paste a query from the dataset's SQL document into QUERY below, then run:

    .venv/bin/python examples/19-sql-by-business-question/02_run_any_sql.py

The seed is the file the generator built. Nothing here can write to it: the
query is validated as a SELECT first, and the engine rolls back regardless.
"""

from agent_app.dataset import local_sqlite_engine
from agent_app.sql_utils import execute_sql_query

# Replace this with any query you want to try.
QUERY = """
SELECT
    i.industry_name,
    COUNT(l.id) AS loan_count,
    ROUND(SUM(l.approved_amount), 0) AS total_approved
FROM loan l
JOIN customer c ON l.customer_id = c.id
JOIN industry i ON c.industry_id = i.id
GROUP BY i.industry_name
ORDER BY total_approved DESC
LIMIT 10
"""


def main() -> None:
    print(execute_sql_query(engine=local_sqlite_engine(), sql=QUERY))


if __name__ == "__main__":
    main()
