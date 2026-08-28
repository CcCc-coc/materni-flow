# -*- coding: utf-8 -*-

"""
Monthly LLM spend cap, backed by one DynamoDB row per (deployment, month).

**Off by default** (``Config.quota_enabled``): it needs a DynamoDB table that
does not exist until someone creates it, and it is meant for a public
deployment, where the person paying is not the person typing.

The entry points check that flag themselves and return early, so a caller never
has to guard the call. Same for infrastructure faults: **metering must never
deny service**, so a DynamoDB failure is logged and swallowed here rather than
in every caller. The one thing that does propagate is
:class:`QuotaExceededError`, which is the answer, not a fault.

Every function takes ``boto_ses`` and ``config`` explicitly rather than reaching
for the ``one`` singleton, which is what lets a test drive this with a stub and
no AWS.
"""

import typing as T
import datetime

from .utils import debug

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
    """
    The DynamoDB table holding the counters.

    That the name is set is guaranteed by ``Config.__post_init__``, which
    refuses to build a config with the cap on and no table named.
    """
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
    Atomically add to the current month's counters. No-op when the cap is off.

    ``ADD`` upserts and treats an absent numeric attribute as 0, which is what
    makes this safe under concurrency: a read-then-write would lose updates
    whenever two requests overlap, and on a public deployment they will.
    """
    if not config.quota_enabled:
        return
    if app_id is None:
        app_id = get_app_id(config)
    try:
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
    except Exception as e:
        # Losing a count is cheaper than failing a reply the user already paid for.
        debug(f"[quota] increment failed: {e}")


def check_quota(
    boto_ses: T.Any,
    config: "Config",
    app_id: str | None = None,
) -> dict[str, int] | None:
    """
    Raise :class:`QuotaExceededError` if any of the three caps is reached.

    Checked before the model is called rather than after, because the point is
    to not spend the tokens.

    Returns the current counters, or None when the cap is off or the counters
    could not be read -- neither is a reason to refuse the request.
    """
    if not config.quota_enabled:
        return None
    if app_id is None:
        app_id = get_app_id(config)
    try:
        usage = get_usage(boto_ses, config, app_id)
    except Exception as e:
        # Metering is broken, which is not the user's problem. Note it and let
        # the request through; the alternative is an outage caused by bookkeeping.
        debug(f"[quota] check failed, allowing request: {e}")
        return None
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
