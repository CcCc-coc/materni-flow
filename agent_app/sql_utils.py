# -*- coding: utf-8 -*-

"""
How SQL is executed and handed to the agent.

Pure functions -- ``engine`` is the first parameter, nothing here reaches for
``self``. The module owns one promise: **a query run through
:func:`execute_sql_query` cannot change the database.**
"""

import re
import typing as T

import sqlalchemy as sa
import sqlalchemy.exc as sa_exc
from tabulate import tabulate


def new_sqlite_engine(path: str) -> sa.Engine:
    """
    Open a SQLite database with transactions the caller can actually roll back.

    Lives here rather than with the other engines because it exists to hold up
    :func:`execute_sql_query`'s guarantee, and a safety setting stored away from
    the thing it protects is one the next refactor drops without noticing.

    ``execute_sql_query`` protects the data by always rolling back, which needs
    a transaction to be open. pysqlite decides that by sniffing the statement's
    first keyword, and it does not recognise ``WITH`` -- so a CTE-prefixed write
    runs in autocommit and lands on disk with nothing to roll back.

    Turning ``isolation_level`` off stops the driver guessing, and emitting
    ``BEGIN`` ourselves puts every statement -- CTE-prefixed writes and DDL
    included -- inside a transaction the caller can discard. This is the recipe
    from SQLAlchemy's own pysqlite notes.

    :param path: Database file path, or ``":memory:"``.
    """
    engine = sa.create_engine(f"sqlite:///{path}")

    @sa.event.listens_for(engine, "connect")
    def _disable_pysqlite_implicit_begin(dbapi_connection, _):
        dbapi_connection.isolation_level = None

    @sa.event.listens_for(engine, "begin")
    def _emit_explicit_begin(connection):
        connection.exec_driver_sql("BEGIN")

    return engine


def format_result(
    result: T.Union["sa.CursorResult", "sa.Result"],
) -> str:
    """
    Format a SQL result as a Markdown table.

    Markdown beats JSON here on every axis that matters: it costs roughly a
    quarter fewer tokens, it matches what the model saw during training, and it
    stays readable when a human opens the log to work out what went wrong.
    """
    records = result.fetchall()
    if len(records) == 0:
        return "No result"

    rows = [list(result.keys())]
    rows.extend(list(record) for record in records)
    return tabulate(rows, headers="firstrow", tablefmt="pipe", floatfmt=".4f")


def ensure_valid_select_query(query: str):
    """
    Reject the obvious non-query before spending a database round trip on it.

    **This is not the safety boundary.** What actually protects the data is that
    every agent query runs inside a transaction that is always rolled back (see
    :func:`execute_sql_query`). This check exists so that a model which writes
    ``UPDATE`` gets a fast, readable error telling it what to do instead, rather
    than a driver exception.

    It is deliberately one rule and no keyword denylist. A denylist reads the
    query as a string and cannot tell code from data, so it rejects perfectly
    legal queries -- ``WHERE note = 'do not delete'`` -- while still missing the
    dangerous things that hide inside a legal ``SELECT``. Every false rejection
    costs a full model round trip and pushes the model toward stranger SQL to
    get around it, which is the worse failure of the two.

    ``WITH`` is accepted because every non-trivial analysis is a CTE. A write
    smuggled in behind one (SQLite does accept ``WITH x AS (...) DELETE ...``)
    executes and is then discarded with the transaction.

    :raises ValueError: if the query starts with anything but SELECT or WITH.
    """
    if not re.match(r"^(SELECT|WITH)\b", query.strip(), re.IGNORECASE):
        raise ValueError(
            "Invalid query: this agent is read-only, start with SELECT or WITH"
        )


def execute_sql_query(
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
    us today. On SQLite it additionally requires the engine from
    :func:`new_sqlite_engine`; on MySQL it would not hold for DDL, which commits
    implicitly.

    **Every failure is returned as text, never raised.** The caller is an LLM
    tool: a traceback ends the turn, whereas a sentence describing the problem
    lets the model fix its own SQL and try again.

    :param engine: SQLAlchemy engine connected to the database.
    :param sql: Raw SQL query string to execute.

    :return: The result as a Markdown table, or an ``Error: ...`` message.
    """
    try:
        ensure_valid_select_query(sql)
    except ValueError as e:
        return f"Error: {e}"

    stmt = sa.text(sql)
    with engine.connect() as conn:
        try:
            result = conn.execute(stmt)
        except sa_exc.StatementError as e:
            # ``_message()`` is private, but it is the only way to get the
            # driver's sentence without the SQL, the bound parameters and the
            # docs URL that ``str(e)`` appends -- a few hundred wasted tokens on
            # every mistyped query. If a SQLAlchemy upgrade removes it, fall
            # back to ``str(e)``; the tool degrades, it does not break.
            return f"Error executing query: {e._message()}"
        except Exception as e:  # pragma: no cover
            return f"Error executing query: {e}"

        try:
            return format_result(result)
        except Exception as e:  # pragma: no cover
            return f"Error formatting result: {e}"
        finally:
            # Written out rather than left to the context manager's implicit
            # rollback: a safety guarantee nobody can see in the code is one the
            # next refactor deletes by adding a commit.
            conn.rollback()
