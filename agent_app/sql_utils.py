# -*- coding: utf-8 -*-

import re
import typing as T

import sqlalchemy as sa
import sqlalchemy.exc as sa_exc
from tabulate import tabulate


def format_result(
    result: T.Union["sa.CursorResult", "sa.Result"],
) -> str:
    """
    Format SQL query result into a Markdown table.

    .. note::

        Markdown tables are the optimal format for presenting SQL query results to LLMs,
        offering the best combination of token efficiency, comprehension, and maintainability.

        - Token Efficiency: Uses 24% fewer tokens than JSON, reducing API costs
            and fitting more data within context limits
        - Natural LLM Comprehension: Aligns with LLM training data patterns,
            enabling better understanding compared to nested JSON/XML structures
        - Balanced Readability: Maintains both machine parsability and human readability
            for seamless debugging and maintenance
    """
    records = result.fetchall()
    if len(records) == 0:
        return "No result"

    rows = list()
    columns = result.keys()
    rows.append(columns)
    for record in records:
        rows.append(list(record))

    text = tabulate(
        rows,
        headers="firstrow",
        tablefmt="pipe",
        floatfmt=".4f",
    )
    return text


def ensure_valid_select_query(query: str):
    """
    Reject the obvious non-query before spending a database round trip on it.

    **This is not the safety boundary.** What actually protects the data is that
    every agent query runs inside a transaction that is always rolled back (see
    :func:`execute_and_print_result`). This check exists so that a model which
    writes ``UPDATE`` gets a fast, readable error telling it what to do instead,
    rather than a driver exception.

    It is deliberately one rule and no keyword denylist. A denylist reads the
    query as a string and cannot tell code from data, so it rejects perfectly
    legal queries -- ``WHERE note = 'do not delete'`` -- while still missing the
    dangerous things that hide inside a legal ``SELECT``. Every false rejection
    costs a full model round trip and pushes the model toward stranger SQL to
    get around it, which is the worse failure of the two.

    ``WITH`` is accepted because every non-trivial analysis is a CTE. A write
    smuggled in behind one (SQLite does accept ``WITH x AS (...) DELETE ...``)
    executes and is then discarded with the transaction.
    """
    if not re.match(r"^(SELECT|WITH)\b", query.strip(), re.IGNORECASE):
        raise ValueError(
            "Invalid query: this agent is read-only, start with SELECT or WITH"
        )


def execute_and_print_result(
    engine: "sa.Engine",
    sql: str,
) -> str:
    """
    Execute a read-only query and return the result as a Markdown table.

    The transaction is **always** rolled back. That, not the string check above,
    is what makes this read-only: a write that slips past the check still runs
    against a transaction nobody ever commits, so it never reaches disk. The
    guarantee costs nothing (SQLAlchemy 2.0 does not autocommit), needs no
    dependency, and works on every dialect rather than just the one in front of
    us today.

    Two caveats worth knowing. On SQLite the driver decides whether to open a
    transaction by sniffing the statement's first keyword, and it does not
    recognise ``WITH`` -- so the engine has to be built with an explicit
    ``BEGIN`` (see ``one_02_db.py``) or a CTE-prefixed write commits itself. And
    on MySQL, DDL commits implicitly and cannot be rolled back at all.

    :param engine: SQLAlchemy engine instance connected to the database.
    :param sql: Raw SQL query string to execute.

    :return: The query result formatted as a Markdown table string.
    """
    try:
        ensure_valid_select_query(sql)
    except ValueError as e:  # pragma: no cover
        return f"Error: {e}"

    stmt = sa.text(sql)
    with engine.connect() as conn:
        try:
            result = conn.execute(stmt)
        except sa_exc.OperationalError as e:  # pragma: no cover
            return f"Error executing query: {e._message()}"
        except Exception as e:  # pragma: no cover
            return f"Error executing query: {e}"

        try:
            text = format_result(result)
        except Exception as e:  # pragma: no cover
            return f"Error formatting result: {e}"
        finally:
            # Written out rather than left to the context manager's implicit
            # rollback: a safety guarantee nobody can see in the code is one the
            # next refactor deletes by adding a commit.
            conn.rollback()

        print(text)
        return text
