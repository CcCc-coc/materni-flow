# -*- coding: utf-8 -*-

"""
The dataset's headline question, run against the local SQLite seed.

Grade C is priced as if 6% of those loans will default. This query asks what
share actually did, so the two numbers can be put side by side.

Run it:

    .venv/bin/python examples/19-sql-by-business-question/01_pricing_gap.py
"""

from agent_app.dataset import local_sqlite_engine
from agent_app.sql_utils import execute_sql_query

# LEFT JOIN, not INNER JOIN: a loan that never defaulted has no row in
# default_event, and INNER JOIN would drop it. The denominator has to keep
# every loan, otherwise the rate comes out as 100%.
#
# 100.0 rather than 100: integer division would floor every rate to 0.
SQL = """
SELECT
    rg.grade_code,
    rg.interest_rate,
    rg.implied_default_rate,
    COUNT(l.id) AS loan_count,
    ROUND(100.0 * COUNT(de.id) / COUNT(l.id), 2) AS actual_default_rate,
    ROUND(rg.implied_default_rate - 100.0 * COUNT(de.id) / COUNT(l.id), 2) AS pricing_gap
FROM loan l
JOIN risk_grade rg ON l.risk_grade_id = rg.id
LEFT JOIN default_event de ON de.loan_id = l.id
GROUP BY rg.grade_code, rg.interest_rate, rg.implied_default_rate
ORDER BY rg.grade_code
"""


def main() -> None:
    # execute_sql_query returns failures as text rather than raising, because
    # its usual caller is a model. Here a human is reading, so say nothing more
    # when the query did not run.
    result = execute_sql_query(engine=local_sqlite_engine(), sql=SQL)
    print(result)
    if not result.startswith("Error"):
        print(
            "\nRead the last column. A negative pricing gap means the grade "
            "defaults\nmore than its price assumed, so those loans were "
            "underpriced."
        )


if __name__ == "__main__":
    main()
