# -*- coding: utf-8 -*-

"""
Translation layer between the Vercel AI SDK frontend and the Strands Agent.

The frontend and the backend describe a conversation differently, and this
module is the only place that knows both dialects:

- **Inbound** -- the frontend POSTs a :class:`RequestBody` whose messages are
  lists of typed *parts* (text, reasoning, ...). The agent wants messages whose
  content is a list of ``{"text": ...}`` blocks.
- **Outbound** -- the agent hands back a finished string. The frontend expects
  the AI SDK v5 Data Stream Protocol over Server-Sent Events.

Nothing in here is provider-specific. The message shape the agent uses happens
to be the one AWS invented for the Bedrock Converse API, and Strands kept it
across every provider it supports -- so switching ``LLM_PROVIDER`` between
bedrock, openai, anthropic, and google does not touch this file. Keep it that
way: if provider-specific code ever needs to exist, it belongs next to the
model construction in ``one_04_agent.py``, not here.

The request/response data model itself lives in
``agent_app/vendor/vercel_ai_sdk.py``.
"""

import sys
import json
import uuid

from fastapi import Request

from .utils import debug
from .vendor.vercel_ai_sdk import RequestBody


# ------------------------------------------------------------------------------
# Inbound: frontend JSON -> agent input
# ------------------------------------------------------------------------------
def get_last_user_message_text(request_body: RequestBody) -> str | None:
    """
    Extract the text of the newest user message -- the question to answer now.

    The AI SDK always puts the message being sent at the end of the list, so
    this is the last entry rather than a search by role.

    Args:
        request_body: The parsed AI SDK request body.

    Returns:
        The text the user just typed, or ``None`` if there is none. Returning
        ``None`` rather than raising lets the caller answer with a readable
        error instead of a 500 -- an empty request is a client bug, and the
        useful response to it is a message, not a stack trace.
    """
    if not request_body.messages:
        return None

    # A message can hold several parts; join only the visible-text ones, so a
    # reasoning block never gets mistaken for what the user said.
    text = "".join(part.text for part in request_body.messages[-1].text_parts())
    return text or None


def request_body_to_agent_history(request_body: RequestBody) -> list[dict]:
    """
    Convert the conversation so far into the agent's message format.

    The last message is excluded on purpose: that is the question being asked
    right now, which goes to the agent as its input rather than as history.

    Reasoning parts are dropped. The agent does not benefit from re-reading its
    own earlier thinking, and those blocks are long -- they would be resent, and
    paid for, on every subsequent turn.

    Args:
        request_body: The parsed AI SDK request body.

    Returns:
        Messages shaped as ``{"role": ..., "content": [{"text": ...}, ...]}``,
        ready to load into ``agent.messages``. Messages left with no text at
        all are skipped rather than sent as empty content, which providers
        reject.
    """
    messages = []

    for message in request_body.messages[:-1]:
        content = [{"text": part.text} for part in message.text_parts()]
        if content:
            messages.append({"role": message.role, "content": content})

    return messages


# ------------------------------------------------------------------------------
# Outbound: agent output -> AI SDK Data Stream Protocol (SSE)
#
# Every event is one `data: <json>` line followed by a blank line. Text and
# reasoning are each sent as a three-phase sequence -- start, delta, end -- so
# that the UI can open a block, fill it, and close it. We send one delta
# holding the whole string because the agent has already finished by the time
# we get here; true token-by-token streaming would emit many deltas instead,
# and nothing else about the protocol would change.
# ------------------------------------------------------------------------------
def _sse(**payload) -> str:
    """Format one Server-Sent Event line from a JSON payload."""
    return f"data: {json.dumps(payload)}\n\n"


def ai_sdk_message_with_reasoning_generator(reasoning_text: str, output_text: str):
    """
    Stream a finished answer, with its thinking, as AI SDK v5 SSE events.

    Args:
        reasoning_text: The model's thinking, rendered as a collapsible block.
            Falsy values skip the reasoning events entirely -- an empty block
            shows up in the UI as a stray toggle with nothing inside it.
        output_text: The answer itself.

    Yields:
        SSE-formatted strings, in protocol order: reasoning (optional), then
        text, then the finish marker.
    """
    if reasoning_text:
        # Each block needs an id so the frontend can tell concurrent blocks
        # apart and match every delta to the block it belongs to.
        reasoning_id = str(uuid.uuid4())
        yield _sse(type="reasoning-start", id=reasoning_id)
        yield _sse(type="reasoning-delta", id=reasoning_id, delta=reasoning_text)
        yield _sse(type="reasoning-end", id=reasoning_id)

    text_id = str(uuid.uuid4())
    yield _sse(type="text-start", id=text_id)
    yield _sse(type="text-delta", id=text_id, delta=output_text)
    yield _sse(type="text-end", id=text_id)

    # Ends the message. Without it the UI keeps showing a spinner forever.
    yield _sse(type="finish", finishReason="stop")

    # SSE stream termination marker, defined by the protocol rather than by us.
    yield "data: [DONE]\n\n"


# ------------------------------------------------------------------------------
# Debugging
# ------------------------------------------------------------------------------
async def debug_ai_sdk_request(request: Request) -> dict:
    """
    Log an incoming request, and return its parsed JSON body.

    This both logs and returns the body because a request body can only be read
    once -- reading it here and throwing it away would leave the caller with
    nothing to parse.

    Args:
        request: The raw FastAPI request.

    Returns:
        The decoded JSON body, ready to pass to ``RequestBody(**body)``.
    """
    debug("====== Incoming request")
    debug("------ Request Headers")
    for key, value in request.headers.items():
        debug(f"{key}: {value}")
    debug("------ Request Body")
    request_body_data = await request.json()
    debug(json.dumps(request_body_data, indent=2, ensure_ascii=False))
    sys.stderr.flush()
    return request_body_data
