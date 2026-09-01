# -*- coding: utf-8 -*-

"""
The same three-turn conversation, with the bookkeeping wrapped in a class.

Script 01 managed the history by hand: append, send, append, every turn. That
works, and it also means every caller has to get the order right and remember
step three. This file moves those three steps inside one method, so the caller
cannot get them wrong.

One instance == one conversation. Create a second instance and it starts from a
blank history with no knowledge of the first, which is exactly how you would
serve two different users at the same time.

This one is written against OpenAI. Pointing it at another vendor means
changing three lines and nothing else: where the client is built, how the call
is made, and how the answer is unwrapped. That is precisely what this app's own
provider layer does, once, for all four vendors.

Run it:
    .venv/bin/python examples/16-multi-turn-and-caching/04_chat_session.py
"""

import dataclasses

from openai import OpenAI

from agent_app.api import one
from agent_app.constants import DEFAULT_MODEL_ID, LlmProviderEnum

MODEL_ID = DEFAULT_MODEL_ID[LlmProviderEnum.OPENAI.value]
SYSTEM_PROMPT = "You are a helpful assistant. Answer in one short sentence."


@dataclasses.dataclass
class ChatSession:
    """
    One ongoing conversation with an OpenAI model.

    Attributes:
        model_id: Which model to talk to.
        system_prompt: The standing instruction sent on every call. Stored once
            here rather than passed to every ``ask()``, because it does not
            change during a conversation.
    """

    model_id: str = MODEL_ID
    system_prompt: str = SYSTEM_PROMPT

    # The history, identical in content to the list script 01 managed by hand.
    # It has just moved inside the object.
    #
    # `init=False` keeps it out of the constructor: it is internal state, not
    # something a caller supplies. `default_factory=list` gives each instance
    # its OWN list -- writing `_messages: list = []` would be a classic Python
    # bug where every instance shares one list and every conversation bleeds
    # into every other.
    _messages: list[dict] = dataclasses.field(init=False, default_factory=list)

    # Built once per session and reused, for the same reason script 01 built
    # the client outside the loop.
    _client: OpenAI = dataclasses.field(init=False, default=None)

    def __post_init__(self):
        """Runs automatically right after the dataclass constructor."""
        api_key = one.config.openai_api_key
        if not api_key:
            raise SystemExit(
                "OPENAI_API_KEY is not set. Add it to the .env file at the repo root."
            )
        self._client = OpenAI(api_key=api_key)
        # OpenAI carries the system prompt inside the message list, so seed it
        # as entry zero. Written once, never touched again.
        self._messages.append({"role": "system", "content": self.system_prompt})

    def ask(self, question: str) -> str:
        """
        Say something, get the reply as plain text.

        This one method performs all three steps from script 01, so no caller
        can get the order wrong or skip one.
        """
        # Step 1: append the question.
        self._messages.append({"role": "user", "content": question})

        # Step 2: send the whole history.
        response = self._client.chat.completions.create(
            model=self.model_id,
            messages=self._messages,
        )

        # Step 3: append the reply, so the next ask() can see it.
        answer = response.choices[0].message.content
        self._messages.append({"role": "assistant", "content": answer})

        return answer

    @property
    def turn_count(self) -> int:
        """How many exchanges have happened. Handy for trimming later."""
        return (len(self._messages) - 1) // 2


# True only when this file is run directly, false when it is imported. It keeps
# the demo from firing if someone later does `from ... import ChatSession`.
if __name__ == "__main__":
    session = ChatSession()

    for question in [
        "My favorite number is 7. Just acknowledge it.",
        "Double my favorite number.",
        "What was my favorite number before you doubled it?",
    ]:
        print("\nYou:", question)
        print("AI:", session.ask(question))

    print(f"\n===== Done: {session.turn_count} turns =====")

    # A second session knows nothing about the first. This is the whole point
    # of one-instance-per-conversation.
    other = ChatSession()
    print("\nA fresh session, asked the same follow-up:")
    print("AI:", other.ask("What was my favorite number before you doubled it?"))
