# -*- coding: utf-8 -*-

"""
Drive the spend cap end to end against a DynamoDB that runs inside this process.

moto is a real implementation of the DynamoDB API, not a stand-in that agrees
with whatever this script does. So the counters really accumulate, and a table
that does not exist really raises the exception botocore would raise. That is
the whole reason the tests use it instead of a hand-written double.

Needs no AWS account, no credentials and no network.

Run it:
    .venv/bin/python examples/33-the-spend-cap/01_watch_the_counters.py
"""

import os

import boto3
from moto import mock_aws

from agent_app.config import Config
from agent_app.quota import (
    ATTR_INPUT_TOKEN,
    ATTR_INVOKE,
    ATTR_OUTPUT_TOKEN,
    QuotaExceededError,
    check_quota,
    get_app_id,
    get_usage,
    increment_usage,
)

REGION = "us-east-1"
TABLE = "demo-quota"

# Fake credentials, so that a mock that failed to engage still cannot reach a
# real account.
for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
    os.environ[name] = "testing"
os.environ["AWS_DEFAULT_REGION"] = REGION


def counters(client, config, app_id):
    u = get_usage(client, config, app_id)
    return (u[ATTR_INVOKE], u[ATTR_INPUT_TOKEN], u[ATTR_OUTPUT_TOKEN])


with mock_aws():
    client = boto3.client("dynamodb", region_name=REGION)
    client.create_table(
        TableName=TABLE,
        KeySchema=[{"AttributeName": "app_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "app_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    on = Config(
        schema_name="acme_widgets",
        llm_provider="openai",
        quota_enabled=True,
        dynamodb_table_name_quota=TABLE,
        quota_max_invoke_per_month=3,
        quota_max_input_token_per_month=10_000,
        quota_max_output_token_per_month=10_000,
    )
    app_id = get_app_id(on)

    print("=" * 78)
    print("1. The partition key is three parts")
    print("=" * 78)
    print(f"\n   {app_id}\n")
    print("   scaffold : dataset : month")
    print("   The month is in the key, so a new month starts from zero on its own.")
    print("   Nobody has to remember to reset anything.\n")

    print("=" * 78)
    print("2. A month with no traffic reads as three zeros, not an error")
    print("=" * 78)
    print(f"\n   {counters(client, on, app_id)}   (invoke, input, output)\n")
    print("   There is no row yet. An absent attribute reads as zero.\n")

    print("=" * 78)
    print("3. The counters really add up")
    print("=" * 78)
    print()
    for i in (1, 2, 3):
        increment_usage(client, on, input_tokens=100, output_tokens=40)
        print(f"   after increment {i}:  {counters(client, on, app_id)}")
    print()
    print("   This is what a hand-written double cannot prove. A double can only")
    print("   record that update_item was called; moto actually applies the ADD,")
    print("   which is what makes 'we do not read-then-write' testable.\n")

    print("=" * 78)
    print("4. The cap is checked BEFORE the model is called")
    print("=" * 78)
    print()
    print(f"   the invoke cap is {on.quota_max_invoke_per_month}, and we are at "
          f"{counters(client, on, app_id)[0]}")
    try:
        check_quota(client, on, app_id)
        print("   check_quota passed (unexpected)\n")
    except QuotaExceededError as e:
        print(f"   check_quota RAISED  {e}\n")
    print("   The caller turns this into a fixed sentence and returns it.")
    print("   The refusal path spends nothing: no model call at all.\n")

    print("=" * 78)
    print("5. Broken metering must NOT refuse service")
    print("=" * 78)
    print()
    broken = Config(
        schema_name="acme_widgets",
        llm_provider="openai",
        quota_enabled=True,
        dynamodb_table_name_quota="this-table-does-not-exist",
    )
    result = check_quota(client, broken, get_app_id(broken))
    print(f"   check_quota against a missing table returned {result!r}")
    increment_usage(client, broken, input_tokens=1, output_tokens=1)
    print("   increment_usage against a missing table did not raise either")
    print()
    print("   Both swallowed a real ResourceNotFoundException. Losing a count is")
    print("   cheaper than failing a reply the user already waited for. Note the")
    print("   asymmetry: QuotaExceededError is an ANSWER and is allowed out;")
    print("   an infrastructure fault is not, and is not.\n")

    print("=" * 78)
    print("6. With the cap off, neither entry point touches DynamoDB")
    print("=" * 78)
    print()
    off = Config(schema_name="acme_widgets", llm_provider="openai", quota_enabled=False)

    class Explode:
        def __getattr__(self, name):
            raise AssertionError(f"the cap is off, nothing should call {name}()")

    print(f"   check_quota returned {check_quota(Explode(), off)!r}")
    increment_usage(Explode(), off, input_tokens=1, output_tokens=1)
    print("   increment_usage returned without calling anything")
    print()
    print("   The switch lives inside the module that owns the feature, so no")
    print("   caller has to remember to wrap these in an `if`. A second caller")
    print("   that forgot would fire a real request with the cap turned off.")
