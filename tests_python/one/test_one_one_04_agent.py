# -*- coding: utf-8 -*-

"""
Test for the agent's read-only tools.

These call the tool methods directly, the same way the strands agent does at
runtime, but without building a model or an Agent -- so no API key, no network,
no tokens spent. The tools only touch the local SQLite database and the
filesystem, which is what makes that possible.

The write-operation tools are not covered here: they are commented out of the
agent's tool list and target tables that do not exist in this dataset.
"""

from agent_app.one.one_00_main import one
from agent_app.paths import path_enum


class TestReadOnlyTools:
    def test_get_database_schema(self):
        """The schema tool returns the encoded schema, including real tables."""
        result = one.tool_get_database_schema()
        assert isinstance(result, str)
        assert "loan" in result
        assert "customer" in result

    def test_execute_sql_query(self):
        """A valid SELECT comes back as a Markdown table."""
        result = one.tool_execute_sql_query(sql="SELECT COUNT(*) AS n FROM loan")
        assert "|" in result  # Markdown table pipes
        assert "n" in result

    def test_execute_sql_query_no_rows(self):
        """A query matching nothing says so instead of returning an empty table."""
        result = one.tool_execute_sql_query(sql="SELECT 1 WHERE 1 = 0")
        assert result == "No result"

    def test_execute_sql_query_rejects_non_select(self):
        """Write statements are refused: this agent is read-only."""
        result = one.tool_execute_sql_query(sql="DROP TABLE loan")
        assert "Invalid query" in result

    def test_execute_sql_query_reports_bad_sql(self):
        """A broken query returns an error string rather than raising."""
        result = one.tool_execute_sql_query(sql="SELECT * FROM no_such_table")
        assert result.startswith("Error")

    def test_write_debug_report(self):
        """The debug report tool writes the file and returns its path."""
        content = "# Debug Report\n\nHello from the test suite.\n"
        result = one.tool_write_debug_report(content=content)
        assert path_enum.path_debug_report_md.exists()
        assert path_enum.path_debug_report_md.read_text(encoding="utf-8") == content
        assert str(path_enum.path_debug_report_md) in result


if __name__ == "__main__":
    from agent_app.tests import run_cov_test

    run_cov_test(
        __file__,
        "agent_app.one.one_04_agent",
        preview=False,
    )
