# -*- coding: utf-8 -*-

"""
Tests for the monthly spend cap.

Driven with a stub boto3 session rather than a real table: the logic worth
testing is the arithmetic and the boundary, and neither needs AWS. That the
module takes ``boto_ses`` and ``config`` as plain arguments is what makes this
possible.
"""

import datetime

import pytest

from agent_app.quota import ATTR_INPUT_TOKEN
from agent_app.quota import ATTR_INVOKE
from agent_app.quota import ATTR_OUTPUT_TOKEN
from agent_app.quota import QuotaExceededError
from agent_app.quota import check_quota
from agent_app.quota import get_app_id
from agent_app.quota import get_usage
from agent_app.quota import increment_usage


class StubTable:
    """Records what was asked of DynamoDB, and answers with a canned item."""

    def __init__(self, item=None):
        self.item = item
        self.updates = []

    def get_item(self, Key):
        return {"Item": self.item} if self.item is not None else {}

    def update_item(self, **kwargs):
        self.updates.append(kwargs)


class StubSession:
    def __init__(self, table):
        self._table = table

    def resource(self, name):
        assert name == "dynamodb"
        return self

    def Table(self, name):
        self._table.name = name
        return self._table


class StubConfig:
    def __init__(self, **overrides):
        self.dynamodb_table_name_quota = "quota-table"
        self.quota_max_invoke_per_month = 100
        self.quota_max_input_token_per_month = 1_000
        self.quota_max_output_token_per_month = 500
        for k, v in overrides.items():
            setattr(self, k, v)


class TestAppId:
    def test_shape_is_project_and_month(self):
        """The key namespaces by project so one table can serve several."""
        moment = datetime.datetime(2026, 3, 9, tzinfo=datetime.timezone.utc)
        app_id = get_app_id(moment)
        assert app_id.endswith("-2026-03")

    def test_month_rolls_over(self):
        """A new month is a new row, so usage resets without anyone acting."""
        jan = get_app_id(datetime.datetime(2026, 1, 31, tzinfo=datetime.timezone.utc))
        feb = get_app_id(datetime.datetime(2026, 2, 1, tzinfo=datetime.timezone.utc))
        assert jan != feb


class TestGetUsage:
    def test_missing_row_reads_as_zero(self):
        """A month with no traffic has no row. That is not an error."""
        session = StubSession(StubTable(item=None))
        usage = get_usage(session, StubConfig(), app_id="x")
        assert usage == {ATTR_INVOKE: 0, ATTR_INPUT_TOKEN: 0, ATTR_OUTPUT_TOKEN: 0}

    def test_existing_row_is_coerced_to_int(self):
        """DynamoDB hands numbers back as Decimal; callers compare them to ints."""
        from decimal import Decimal

        table = StubTable(item={ATTR_INVOKE: Decimal("7"), ATTR_INPUT_TOKEN: Decimal("12")})
        usage = get_usage(StubSession(table), StubConfig(), app_id="x")
        assert usage[ATTR_INVOKE] == 7
        assert isinstance(usage[ATTR_INVOKE], int)
        assert usage[ATTR_OUTPUT_TOKEN] == 0

    def test_missing_table_name_says_so(self):
        """Enabling the cap without configuring a table is a setup error."""
        config = StubConfig(dynamodb_table_name_quota=None)
        with pytest.raises(ValueError, match="DYNAMODB_TABLE_NAME_QUOTA"):
            get_usage(StubSession(StubTable()), config, app_id="x")


class TestIncrementUsage:
    def test_uses_atomic_add(self):
        """
        ADD upserts and treats a missing attribute as zero. A read-then-write
        would lose updates whenever two requests overlap, which on a public
        deployment they will.
        """
        table = StubTable()
        increment_usage(StubSession(table), StubConfig(), input_tokens=30, output_tokens=8)
        (call,) = table.updates
        assert call["UpdateExpression"].startswith("ADD ")
        assert call["ExpressionAttributeValues"] == {":i": 1, ":it": 30, ":ot": 8}


class TestCheckQuota:
    def test_under_every_cap_passes(self):
        table = StubTable(item={ATTR_INVOKE: 99, ATTR_INPUT_TOKEN: 999, ATTR_OUTPUT_TOKEN: 499})
        assert check_quota(StubSession(table), StubConfig(), app_id="x")[ATTR_INVOKE] == 99

    @pytest.mark.parametrize(
        "item, expected",
        [
            ({ATTR_INVOKE: 100}, "invoke"),
            ({ATTR_INPUT_TOKEN: 1_000}, "input-token"),
            ({ATTR_OUTPUT_TOKEN: 500}, "output-token"),
        ],
    )
    def test_any_cap_reached_blocks(self, item, expected):
        """Each of the three caps blocks on its own, and says which one it was."""
        table = StubTable(item=item)
        with pytest.raises(QuotaExceededError, match=expected):
            check_quota(StubSession(table), StubConfig(), app_id="x")

    def test_boundary_is_inclusive(self):
        """At exactly the cap the budget is spent, so the next call must not run."""
        under = StubTable(item={ATTR_INVOKE: 99})
        check_quota(StubSession(under), StubConfig(), app_id="x")
        at = StubTable(item={ATTR_INVOKE: 100})
        with pytest.raises(QuotaExceededError):
            check_quota(StubSession(at), StubConfig(), app_id="x")


class TestDefaultOff:
    def test_shipped_config_has_the_cap_disabled(self):
        """
        A student cloning the repo must not need a DynamoDB table to chat.
        This is the assertion that keeps that true.
        """
        from agent_app.config.conf_00_def import Config

        assert Config().quota_enabled is False


if __name__ == "__main__":
    from agent_app.tests import run_cov_test

    run_cov_test(__file__, "agent_app.quota", preview=False)
