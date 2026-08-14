# -*- coding: utf-8 -*-

"""
Tests for splitting an agent turn into reasoning and answer.

These run on hand-built message lists rather than a live agent: the shapes that
break the split are exactly the ones that are hard to provoke on demand from a
real model, so they are written out literally here.
"""

from agent_app.agent_debugger import extract_text_from_messages
from agent_app.agent_debugger import normalize_render_blocks
from agent_app.agent_debugger import parse_response_text


def _assistant(text: str) -> dict:
    return {"role": "assistant", "content": [{"text": text}]}


def _user(text: str) -> dict:
    return {"role": "user", "content": [{"text": text}]}


class TestExtractTextFromMessages:
    def test_answer_in_final_message(self):
        """The ordinary shape: the last assistant message carries the answer."""
        messages = [
            _user("how many rows?"),
            _assistant("<thinking>need the schema</thinking>"),
            _user("<tool result>"),
            _assistant("<thinking>counted them</thinking>\n\nThere are 12 rows."),
        ]
        thinking, answer = parse_response_text(extract_text_from_messages(messages))
        assert "need the schema" in thinking
        assert "counted them" in thinking
        assert answer == "There are 12 rows."

    def test_answer_survives_a_pure_thinking_sign_off(self):
        """
        An agent that answers, writes a debug report, then signs off with nothing
        but <thinking> must still produce an answer.

        Reading the final message unconditionally returned an empty string here,
        and the chat UI rendered a reasoning block with no reply underneath --
        indistinguishable, from the user's side, from a hang.
        """
        messages = [
            _user("which records look wrong?"),
            _assistant("<thinking>need the schema</thinking>"),
            _user("<tool result>"),
            _assistant("<thinking>query returned rows</thinking>\n\n- row 7: -35.1%"),
            _user("<tool result: debug report written>"),
            _assistant("<thinking>The final answer has been provided to the User.</thinking>"),
        ]
        thinking, answer = parse_response_text(extract_text_from_messages(messages))
        assert answer == "- row 7: -35.1%"
        assert "The final answer has been provided" in thinking

    def test_thinking_only_turn_yields_no_answer(self):
        """With no answer text anywhere, there is genuinely nothing to return."""
        messages = [
            _user("hello"),
            _assistant("<thinking>nothing to say</thinking>"),
        ]
        thinking, answer = parse_response_text(extract_text_from_messages(messages))
        assert thinking == "nothing to say"
        assert answer == ""

    def test_start_index_skips_earlier_turns(self):
        """Only messages from start_index onward count toward this turn."""
        messages = [
            _user("first question"),
            _assistant("<thinking>old</thinking>\n\nOld answer."),
            _user("second question"),
            _assistant("<thinking>new</thinking>\n\nNew answer."),
        ]
        thinking, answer = parse_response_text(extract_text_from_messages(messages, 2))
        assert thinking == "new"
        assert answer == "New answer."


class TestNormalizeRenderBlocks:
    def test_chart_tag_becomes_a_fence(self):
        """
        Nova Lite wraps chart payloads in <chart>, generalizing from <thinking>.
        Markdown drops the unknown tag, so the reply announces a chart that is
        not there. Re-fence it.
        """
        text = (
            "<chart>\n"
            '{"type": "bar", "title": "Totals", "categories": ["a"], '
            '"series": [{"name": "x", "values": [1]}]}\n'
            "</chart>\n\n"
            "Here is the chart."
        )
        out = normalize_render_blocks(text)
        assert out.startswith("```chart\n")
        assert "```\n\nHere is the chart." in out
        assert "<chart>" not in out

    def test_mermaid_tag_becomes_a_fence(self):
        text = "<mermaid>\nflowchart LR\n    A --> B\n</mermaid>"
        out = normalize_render_blocks(text)
        assert out == "```mermaid\nflowchart LR\n    A --> B\n```"

    def test_existing_fence_is_untouched(self):
        text = '```chart\n{"type": "bar"}\n```'
        assert normalize_render_blocks(text) == text

    def test_plain_prose_is_untouched(self):
        text = "One group accounts for 40% of the problem records."
        assert normalize_render_blocks(text) == text


if __name__ == "__main__":
    from agent_app.tests import run_cov_test

    run_cov_test(
        __file__,
        "agent_app.agent_debugger",
        preview=False,
    )
