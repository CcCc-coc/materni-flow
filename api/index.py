# -*- coding: utf-8 -*-

"""
FastAPI backend for AI chat powered by Strands Agent.

This module provides the API endpoints that connect the frontend chat UI
to the Strands Agent with write operation capabilities. It implements the
Vercel AI SDK v5 Data Stream Protocol using Server-Sent Events (SSE).

Key components:
- /api/hello: Health check endpoint
- /api/chat: Main chat endpoint that processes messages and returns AI responses
  with both reasoning (thinking) and text content
"""

import os
import sys
import io

# fmt: off
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from agent_app.vendor.vercel_ai_sdk import RequestBody  # Parses AI SDK request format
from agent_app.utils import debug
from agent_app.ai_sdk_adapter import ai_sdk_streaming_response
from agent_app.ai_sdk_adapter import get_last_user_message_text
from agent_app.ai_sdk_adapter import read_request_body
from agent_app.ai_sdk_adapter import request_body_to_agent_history
from agent_app.one.api import one  # Main singleton with agent
from agent_app.agent_response import parse_agent_response
from agent_app.quota import check_quota
from agent_app.quota import increment_usage
from agent_app.quota import QuotaExceededError
# fmt: on

# Add project root to sys.path for module imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

app = FastAPI()

#: Shown when the monthly cap is reached. A constant, not a model call: the
#: whole point is that this path spends nothing.
QUOTA_EXCEEDED_MESSAGE = (
    "This demo runs on a monthly token budget, and it has been used up for this "
    "billing cycle. The chat will start working again when the budget resets at "
    "the beginning of next month. Thanks for trying it out."
)


@app.get("/api/hello")
async def hello_world():
    """
    Health check endpoint for testing FastAPI integration.

    Returns a simple JSON response to verify the API is running.
    """
    return JSONResponse(
        content={
            "message": "Hello from FastAPI!",
            "status": "success",
        },
    )


@app.post("/api/chat")
async def handle_chat_data(request: Request, protocol: str = Query("data")):
    """
    Main chat endpoint that processes user messages and returns AI responses.

    This endpoint uses the Strands Agent to process messages and returns
    responses with both reasoning (thinking) and text content using the
    Vercel AI SDK v5 Data Stream Protocol.

    The agent has access to database tools for:
    - Querying the database schema
    - Running read-only SQL queries against the business database
    - Writing a debug report of its own reasoning

    Args:
        request: The incoming HTTP request containing chat messages
        protocol: Stream protocol version (default: "data" for AI SDK v5)
    """
    # --- Log incoming request for troubleshooting
    request_body_data = await read_request_body(request=request)

    # --- Parse the incoming request into AI SDK format
    request_body = RequestBody(**request_body_data)

    # --- Extract the last user message ---
    last_user_message = get_last_user_message_text(request_body)

    if not last_user_message:
        return ai_sdk_streaming_response("Error: No message content found in request.")

    # --- Get the agent and restore conversation history ---
    agent = one.agent

    # Clear previous messages and restore history from the frontend request.
    # The frontend sends all previous messages in request_body.messages.
    # We convert them to agent format and load them before processing the new message.
    agent.messages.clear()

    # Load conversation history (all messages except the last one, which is the current input)
    history_messages = request_body_to_agent_history(request_body)
    agent.messages.extend(history_messages)

    debug(f"[Agent] Loaded {len(history_messages)} history messages")

    # --- Refuse before spending, if this deployment caps its monthly spend ---
    # A no-op when the cap is off, and it swallows its own infrastructure
    # faults, so the only thing that reaches here is an actual refusal.
    try:
        check_quota(one.dynamodb_client(), one.config)
    except QuotaExceededError as e:
        debug(f"[Quota] blocked: {e}")
        return ai_sdk_streaming_response(QUOTA_EXCEEDED_MESSAGE)

    # Record message count before calling agent (so we only extract new messages)
    msg_count_before = len(agent.messages)

    # Call agent with stdout suppressed (we don't want streaming output in the API)
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        agent_result = agent(last_user_message)
    finally:
        sys.stdout = old_stdout

    # --- Meter what that cost ---
    # NOT metrics.accumulated_usage: strands accumulates that across the
    # lifetime of the Agent instance, and `one.agent` is cached, so reading it
    # would re-count every earlier request in the process. The per-invocation
    # total is on the latest AgentInvocation.
    invocations = getattr(agent_result.metrics, "agent_invocations", None) or []
    usage = invocations[-1].usage if invocations else {}
    increment_usage(
        one.dynamodb_client(),
        one.config,
        input_tokens=int(usage.get("inputTokens", 0) or 0),
        output_tokens=int(usage.get("outputTokens", 0) or 0),
    )

    # --- Extract thinking and answer from agent response ---
    thinking, answer = parse_agent_response(agent.messages, msg_count_before)

    debug(f"[Agent] Thinking: {len(thinking)} chars")
    debug(f"[Agent] Answer: {len(answer)} chars")

    # An empty answer streams an empty text block, so the UI shows a reasoning
    # block with nothing under it and the turn reads as a hang. Say so instead:
    # a visible non-answer is debuggable, silence is not.
    if not answer:
        answer = (
            "I worked through this but did not produce a final message. "
            "The reasoning above has what I found — ask me to restate it."
        )
        debug("[Agent] Empty answer, sent fallback text")

    # --- Return SSE response with reasoning and text ---
    return ai_sdk_streaming_response(answer, reasoning_text=thinking)
