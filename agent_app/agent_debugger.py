# -*- coding: utf-8 -*-

"""
Agent debugging utilities.

This module provides helper functions for debugging agent responses,
extracting thinking process, and formatting multi-turn conversations.

Usage:
    from agent_app.one.one_05_agent_debugger import chat, print_summary

    agent = one.agent
    agent.messages.clear()

    thinking, answer = chat(agent, "Your question here", turn_number=1)
"""

import io
import re
import sys

from strands import Agent


def extract_text_from_messages(
    messages: list,
    start_index: int = 0,
    debug: bool = False,
) -> str:
    """
    Extract <thinking> tags from ALL assistant messages, plus the last real answer text.

    Strands Agent embeds thinking content as <thinking>...</thinking> tags directly in the
    text field of each assistant message. When an agent calls multiple tools, it produces
    multiple assistant messages, each with its own thinking block.

    To get the complete reasoning chain:
    - Collect <thinking> content from ALL assistant messages
    - Take the answer from the last assistant message that actually *has* non-thinking
      text, which is not always the last assistant message overall

    That last distinction is load-bearing. An agent that answers, then calls
    ``write_debug_report``, will often sign off with a message consisting of nothing
    but ``<thinking>`` ("the final answer has been provided to the user"). Reading the
    final message unconditionally yields an empty answer, and the chat UI renders a
    reasoning block with no reply under it, which looks to the user like a hang.

    Args:
        messages: List of message dicts from agent.messages
        start_index: Index to start looking from (use msg_count_before)
        debug: If True, print message structure for debugging

    Returns:
        str: All thinking content wrapped in a single <thinking> tag, followed by
             the final text response.

    Example:
        msg_count_before = len(agent.messages)
        agent("Your question")
        full_text = extract_text_from_messages(agent.messages, msg_count_before)
    """
    thinking_pattern = r"<thinking>(.*?)</thinking>"

    # Collect ALL thinking content from all assistant messages
    all_thinking = []
    # Track the most recent assistant text that survives thinking removal
    last_answer_text = None

    for i, msg in enumerate(messages[start_index:], start=start_index):
        if debug:
            print(f"\n[DEBUG] Message {i}:")
            print(f"  role: {msg.get('role')}")
            content = msg.get("content", [])
            print(f"  content type: {type(content)}")
            if isinstance(content, list):
                for j, item in enumerate(content):
                    if isinstance(item, dict):
                        print(f"    [{j}] keys: {list(item.keys())}")
                    else:
                        print(f"    [{j}] type: {type(item)}")

        if msg.get("role") == "assistant":
            content = msg.get("content", [])
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    text = item["text"]

                    # Extract <thinking> content from this message
                    thinking_matches = re.findall(thinking_pattern, text, re.DOTALL)
                    for match in thinking_matches:
                        if match.strip():
                            all_thinking.append(match.strip())

                    # Keep this as the answer only if something remains once the
                    # thinking is stripped out; a pure-thinking sign-off must not
                    # displace the real answer produced a couple of turns earlier.
                    stripped = re.sub(
                        thinking_pattern, "", text, flags=re.DOTALL
                    ).strip()
                    if stripped:
                        last_answer_text = stripped

    if debug:
        print(f"\n[DEBUG] Collected {len(all_thinking)} thinking blocks from all messages")

    # Build final result
    texts = []

    # Add all thinking wrapped in a single <thinking> tag
    if all_thinking:
        combined_thinking = "\n\n".join(all_thinking)
        texts.append(f"<thinking>{combined_thinking}</thinking>")

    # Add the answer text, already stripped of its <thinking> tags above
    if last_answer_text:
        texts.append(last_answer_text)

    return "\n".join(texts)


def parse_response_text(
    full_text: str,
) -> tuple[str, str]:
    """
    Parse full response text into thinking process and final answer.

    This function separates the agent's thinking (reasoning) from its
    final answer by extracting <thinking> tags.

    Args:
        full_text: Full text including <thinking> tags

    Returns:
        tuple[str, str]: (thinking_process, final_answer)
            - thinking_process: All thinking blocks concatenated
            - final_answer: The response with thinking blocks removed

    Example:
        full_text = "<thinking>Let me analyze...</thinking>The answer is 42."
        thinking, answer = parse_response_text(full_text)
        # thinking = "Let me analyze..."
        # answer = "The answer is 42."
    """
    # Extract all <thinking>...</thinking> blocks
    thinking_pattern = r"<thinking>(.*?)</thinking>"
    thinking_matches = re.findall(thinking_pattern, full_text, re.DOTALL)
    thinking_process = "\n\n".join(match.strip() for match in thinking_matches)

    # Remove <thinking> blocks to get final answer
    final_answer = re.sub(thinking_pattern, "", full_text, flags=re.DOTALL)

    # Clean up orphaned markdown headers (e.g., "## " or "### " with nothing after)
    # These appear when agent streams responses in chunks
    final_answer = re.sub(r"^#{1,6}\s*$", "", final_answer, flags=re.MULTILINE)

    # Clean up multiple newlines
    final_answer = re.sub(r"\n{3,}", "\n\n", final_answer)

    # Strip leading/trailing whitespace
    final_answer = final_answer.strip()

    return thinking_process, final_answer


#: Fenced-block languages the chat UI renders as something other than code.
#: Each is also the tag name a model reaches for when it drifts from the fence.
RENDERABLE_BLOCKS = ("chart", "mermaid")


def normalize_render_blocks(text: str) -> str:
    """
    Rewrite ``<chart>``/``<mermaid>`` tag pairs into the fenced blocks the UI renders.

    The prompt asks for fenced blocks, but smaller models -- Nova Lite in
    particular -- already emit ``<thinking>`` tags and generalize the habit,
    wrapping a perfectly good chart payload in ``<chart>`` instead. Markdown
    then treats that as an unknown HTML tag and drops it, so the reply says
    "here is the chart" above nothing at all.

    Prompt wording alone does not survive a model that small, and the mapping is
    unambiguous, so it is done mechanically here. Content already inside a fence
    is left alone: the tag pattern requires the tag to sit on its own line.

    Args:
        text: The agent's answer text.

    Returns:
        str: The same text with any tag-wrapped renderable block re-fenced.
    """
    for name in RENDERABLE_BLOCKS:
        pattern = rf"^[ \t]*<{name}>[ \t]*\n(.*?)\n[ \t]*</{name}>[ \t]*$"
        text = re.sub(
            pattern,
            lambda m, n=name: f"```{n}\n{m.group(1).strip()}\n```",
            text,
            flags=re.DOTALL | re.MULTILINE,
        )
    return text


def chat(
    agent: Agent,
    message: str,
    turn_number: int = 1,
    verbose: bool = False,
    debug: bool = False,
) -> tuple[str, str]:
    """
    Send a message to the agent and return parsed response.

    This is the main debugging function for multi-turn conversations.
    It handles:
    - Printing formatted turn headers and request
    - Suppressing/showing streaming output
    - Extracting and parsing the response
    - Separating thinking from final answer

    Args:
        agent: The strands Agent instance
        message: User message to send
        turn_number: Turn number for display (default: 1)
        verbose: If True, print raw streaming output; if False, suppress it
        debug: If True, print message structure for debugging

    Returns:
        tuple[str, str]: (thinking_process, final_answer)

    Example:
        from agent_app.one.api import one
        from agent_app.one.one_05_agent_debugger import chat

        agent = one.agent
        agent.messages.clear()

        # Turn 1
        thinking, answer = chat(agent, "What tables are in the database?", turn_number=1)
        results.append(("Schema", thinking, answer))

        # Turn 2 (conversation continues)
        thinking, answer = chat(agent, "Show me the first 5 rows of the largest one", turn_number=2)
        results.append(("Query", thinking, answer))
    """
    # Print turn header
    print("=" * 70)
    print(f"  TURN {turn_number}")
    print("=" * 70)

    # Print request
    print("\n[REQUEST]")
    print("-" * 70)
    print(message)

    # Record message count before calling agent
    msg_count_before = len(agent.messages)

    # Call agent (this prints streaming output)
    if verbose:
        result = agent(message)
    else:
        # Suppress streaming output by redirecting stdout temporarily
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            result = agent(message)
        finally:
            sys.stdout = old_stdout

    # Extract full text from new messages (debug=True to see message structure)
    full_text = extract_text_from_messages(
        agent.messages, msg_count_before, debug=debug
    )

    # Parse into thinking and answer
    thinking, answer = parse_response_text(full_text)

    # Print thinking (if any)
    if thinking:
        print("\n[THINKING]")
        print("-" * 70)
        print(thinking)

    # Print final answer
    print("\n[RESPONSE]")
    print("-" * 70)
    print(answer)

    print("\n")  # Extra spacing between turns

    return thinking, answer


def print_summary(results: list[tuple[str, str, str]]) -> None:
    """
    Print summary of test results.

    Args:
        results: List of tuples (turn_name, thinking, answer)

    Example:
        results = []
        results.append(("Query", thinking1, answer1))
        results.append(("Execute", thinking2, answer2))
        results.append(("Verify", thinking3, answer3))
        print_summary(results)
    """
    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    for turn_name, thinking, answer in results:
        print(f"\n[{turn_name}]")
        print(f"  Thinking: {len(thinking)} chars")
        print(f"  Answer: {len(answer)} chars")


def print_multi_turn_conversation_headers(name: str, n_turns: int) -> None:
    print("\n")
    print("=" * 70)
    print(f"  TEST: {name} - Multi-turn conversation ({n_turns} turns)")
    print("=" * 70)
    print("\n")
