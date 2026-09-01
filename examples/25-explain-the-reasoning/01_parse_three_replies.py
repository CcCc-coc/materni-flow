# -*- coding: utf-8 -*-

"""
Run three hand-made agent replies through the real parser and print what it digs out.

No model call, no server, no key -- the message lists below are written by hand
in exactly the shape strands hands back, so the output is the same every time.

    .venv/bin/python examples/25-explain-the-reasoning/01_parse_three_replies.py

Case 2 is the one worth staring at: the agent answers, then calls a tool, and
its final message contains nothing but thinking. Reading the last message
unconditionally would hand the UI an empty answer.
"""

from agent_app.agent_response import parse_agent_response


def msg(*texts: str) -> dict:
    """One assistant message, in the shape strands builds."""
    return {"role": "assistant", "content": [{"text": t} for t in texts]}


CASES = [
    (
        "1. plain: one message, thinking then answer",
        [msg("<thinking>Grade C looks off.</thinking>Grade C defaults at 9.89%.")],
    ),
    (
        "2. the trap: the answer is NOT in the last message",
        [
            msg("<thinking>Let me check risk_grade.</thinking>"),
            msg("Grade C defaults at 9.89%, well above the 6.0% it was priced at."),
            # The agent signed off by calling write_debug_report, so its final
            # message is thinking and nothing else.
            msg("<thinking>Now I will write the debug report.</thinking>"),
        ],
    ),
    (
        "3. a chart the model wrapped in a tag instead of a fence",
        [msg('Here is the breakdown:\n\n<chart>\n{"type": "bar"}\n</chart>')],
    ),
]


def show(label: str, value: str) -> None:
    print(f"    {label:9} {value!r}" if value else f"    {label:9} <empty>")


def main() -> None:
    for title, messages in CASES:
        thinking, answer = parse_agent_response(messages)
        print(f"--- {title}")
        print(f"    messages  {len(messages)}")
        show("thinking", thinking)
        show("answer", answer)
        print()

    print("Case 2: the answer came from the middle message, not the last one.")
    print("Case 3: the <chart> tag pair was rewritten into a ```chart fence,")
    print("        because markdown drops an unknown tag and shows nothing.")


if __name__ == "__main__":
    main()
