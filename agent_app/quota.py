# -*- coding: utf-8 -*-

"""
Monthly LLM spend cap, backed by one DynamoDB row per (project, month).

Why this exists
---------------

A chat agent that anyone can open is an open invoice: every message spends
tokens on somebody's cloud account. This module keeps that bill bounded by
counting invocations and tokens for the current calendar month and refusing to
start a new one once a cap is reached.

**It is off by default** (``Config.quota_enabled``). A student running the repo
locally is spending their own Bedrock allowance on their own machine and needs
no cap, and enabling it requires a DynamoDB table that does not exist until
someone creates it. It is meant for a public deployment, where the person paying
is not the person typing.

What is configurable and what is not
------------------------------------

Configurable, because it varies by deployment: the on/off flag, the table name,
and the three caps. All live in ``.env`` and are read through ``Config``.

Fixed, because it does not: the item schema below, and the partition key, which
is ``<project name>-YYYY-MM``. The project name comes from
``data/dataset.toml`` -- the same identifier that namespaces this project's
tables in the shared Postgres. One DynamoDB table can hold the counters for
several projects for the same reason one Postgres database can hold their
tables, and giving that identifier a second home in ``.env`` would eventually
give it two different answers.

Why raw boto3 and not an ORM
----------------------------

The item has four attributes and will never have more, so an ORM would buy
nothing here except three dependencies. ``boto3`` is already a core dependency.

Every function takes ``boto_ses`` and ``config`` explicitly rather than reaching
for the ``one`` singleton. That keeps this module importable on its own, lets a
test drive it with a stub, and avoids building a second ``Config`` just to read
three numbers.
"""

import typing as T
import datetime

from .project_config import project_config

if T.TYPE_CHECKING:  # pragma: no cover
    from .config.conf_00_def import Config


#: The DynamoDB attribute names. Fixed on purpose -- see the module docstring.
ATTR_INVOKE = "total_invoke"
ATTR_INPUT_TOKEN = "total_input_token"
ATTR_OUTPUT_TOKEN = "total_output_token"


class QuotaExceededError(RuntimeError):
    """Raised when the current month's usage has hit a configured cap."""


def get_app_id(now: datetime.datetime | None = None) -> str:
    """
    Build the partition key for the current (or given) UTC month.

    Shape is ``<project name>-YYYY-MM``, so a new month starts from zero without
    anyone having to reset anything, and several projects can share one table.

    Returns:
        The partition key, e.g. ``"acme-2026-08"``.
    """
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)
    return f"{project_config.project_name_snake}-{now.year:04d}-{now.month:02d}"


def _table(boto_ses: T.Any, config: "Config") -> T.Any:
    """Return the DynamoDB Table resource holding the counters."""
    if not config.dynamodb_table_name_quota:
        raise ValueError(
            "QUOTA_ENABLED is on but DYNAMODB_TABLE_NAME_QUOTA is not set. "
            "Point it at a DynamoDB table whose partition key is `app_id` (S)."
        )
    return boto_ses.resource("dynamodb").Table(config.dynamodb_table_name_quota)


def get_usage(
    boto_ses: T.Any,
    config: "Config",
    app_id: str | None = None,
) -> dict[str, int]:
    """
    Read the current month's counters.

    A month with no traffic yet has no row at all, which is not an error: it
    reads as three zeros and no write is issued.

    Returns:
        ``{"total_invoke": int, "total_input_token": int, "total_output_token": int}``
    """
    if app_id is None:
        app_id = get_app_id()
    item = _table(boto_ses, config).get_item(Key={"app_id": app_id}).get("Item") or {}
    return {
        ATTR_INVOKE: int(item.get(ATTR_INVOKE, 0)),
        ATTR_INPUT_TOKEN: int(item.get(ATTR_INPUT_TOKEN, 0)),
        ATTR_OUTPUT_TOKEN: int(item.get(ATTR_OUTPUT_TOKEN, 0)),
    }


def increment_usage(
    boto_ses: T.Any,
    config: "Config",
    input_tokens: int,
    output_tokens: int,
    invokes: int = 1,
    app_id: str | None = None,
) -> None:
    """
    Atomically add to the current month's counters.

    Uses ``UpdateItem`` with ``ADD``, which creates the row if it is missing and
    treats an absent numeric attribute as 0 before adding. That matters under
    concurrency: a read-then-write would lose updates whenever two requests
    overlap, and on a public deployment they will.
    """
    if app_id is None:
        app_id = get_app_id()
    _table(boto_ses, config).update_item(
        Key={"app_id": app_id},
        UpdateExpression=(
            f"ADD {ATTR_INVOKE} :i, {ATTR_INPUT_TOKEN} :it, {ATTR_OUTPUT_TOKEN} :ot"
        ),
        ExpressionAttributeValues={
            ":i": int(invokes),
            ":it": int(input_tokens),
            ":ot": int(output_tokens),
        },
    )


def check_quota(
    boto_ses: T.Any,
    config: "Config",
    app_id: str | None = None,
) -> dict[str, int]:
    """
    Raise :class:`QuotaExceededError` if any of the three caps is reached.

    Checked before the model is called rather than after, because the point is
    to not spend the tokens.

    Returns:
        The current counters, when none of the caps has been reached.
    """
    if app_id is None:
        app_id = get_app_id()
    usage = get_usage(boto_ses, config, app_id)
    for attr, cap, label in (
        (ATTR_INVOKE, config.quota_max_invoke_per_month, "invoke"),
        (ATTR_INPUT_TOKEN, config.quota_max_input_token_per_month, "input-token"),
        (ATTR_OUTPUT_TOKEN, config.quota_max_output_token_per_month, "output-token"),
    ):
        if usage[attr] >= cap:
            raise QuotaExceededError(
                f"Monthly {label} cap reached for {app_id}: {usage[attr]} >= {cap}"
            )
    return usage
