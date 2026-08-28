# -*- coding: utf-8 -*-

"""
Monthly LLM spend cap, backed by one DynamoDB row per (deployment, month).

**Off by default** (``Config.quota_enabled``): it needs a DynamoDB table that
does not exist until someone creates it, and it is meant for a public
deployment, where the person paying is not the person typing.

Every function takes ``boto_ses`` and ``config`` explicitly rather than reaching
for the ``one`` singleton, which is what lets a test drive this with a stub and
no AWS.
"""

import typing as T
import datetime

if T.TYPE_CHECKING:  # pragma: no cover
    from .config import Config


#: Identifies this scaffold in a quota table it may share with other codebases.
#: A constant rather than config: it is a fact about *this repository*, not the
#: dataset it serves, so a dataset swap must not touch it.
SCAFFOLD_ID = "learn-bi-agent-app-scaffold"

#: The DynamoDB attribute names. Fixed on purpose -- see the module docstring.
ATTR_INVOKE = "total_invoke"
ATTR_INPUT_TOKEN = "total_input_token"
ATTR_OUTPUT_TOKEN = "total_output_token"


class QuotaExceededError(RuntimeError):
    """Raised when the current month's usage has hit a configured cap."""


def get_app_id(config: "Config", now: datetime.datetime | None = None) -> str:
    """
    Build the partition key: ``<scaffold>:<dataset>:<YYYY-MM>``.

    A new month is a new row, so usage resets without anyone acting. ``:``
    separates the parts because neither a slug nor a schema name can contain
    one, while both contain the ``-`` and ``_`` that appear inside them.
    """
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)
    return f"{SCAFFOLD_ID}:{config.schema_name}:{now.year:04d}-{now.month:02d}"


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

    A month with no traffic has no row, which is not an error: three zeros, and
    no write is issued.
    """
    if app_id is None:
        app_id = get_app_id(config)
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
        app_id = get_app_id(config)
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
        app_id = get_app_id(config)
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
