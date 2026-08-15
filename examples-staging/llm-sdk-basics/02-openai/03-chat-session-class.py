# -*- coding: utf-8 -*-

"""
Step 3 of 3 -- Hide the bookkeeping behind a small ChatSession class.

Example 02 works, but look at what the caller had to remember: seed the system
message, build the right dict shape, append before the call, append again after
the call, then reach through `.choices[0].message.content` to find the text.
That is a lot of ceremony for "ask a question", and every place in your app
that wants to chat has to repeat all of it -- and can forget a step.

None of that ceremony is a decision. It is the same three moves every time, so
it belongs in one place. That is all a class is here: the history becomes an
attribute instead of a loose variable, and the three steps become one method.

The payoff is the call site:

    session = ChatSession()
    print(session.ask("My favorite number is 7."))
    print(session.ask("Double it."))

Two lines, no dicts, no indexing, and it is now impossible to forget to save
the reply. This is the same idea the strands Agent framework applies at a much
larger scale -- worth seeing once at a size you can hold in your head.

The interface below (`ChatSession(...).ask(str) -> str`) is deliberately
IDENTICAL in all four vendor folders, even though the guts differ completely.
That is the second lesson: a thin class of your own lets the rest of your app
stop caring which vendor is behind it.

Requires: uv sync --extra openai   (SDK: openai 2.x)

Credentials: OPENAI_API_KEY in the .env file at the repo root.

Run it:
    .venv/bin/python examples-staging/llm-sdk-basics/02-openai/03-chat-session-class.py
"""

import os
import dataclasses

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

MODEL_ID = "gpt-5.6-luna"
SYSTEM_PROMPT = "You are a helpful assistant. Answer in one short sentence."


@dataclasses.dataclass
class ChatSession:
    """
    One ongoing conversation with an OpenAI model.

    One instance == one conversation. Create a second instance and it starts
    from a blank history, with no knowledge of the first -- which is exactly
    how you would serve two different users at the same time.

    Attributes:
        model_id: Which OpenAI model to talk to.
        system_prompt: The standing instruction sent on every single call.
            It is stored once here rather than passed on every `ask()`, because
            it never changes during a conversation.
    """

    model_id: str = MODEL_ID
    system_prompt: str = SYSTEM_PROMPT

    # The conversation history, identical in content to the `messages` list you
    # managed by hand in example 02 -- it has just moved inside the object.
    #
    # `init=False` keeps it out of the constructor: it is internal state, not
    # something a caller supplies. `default_factory=list` gives each instance
    # its OWN empty list. (Writing `_messages: list = []` would be a classic
    # Python bug: every instance would share one list and every conversation
    # would bleed into every other.)
    _messages: list[dict] = dataclasses.field(init=False, default_factory=list)

    # The SDK client, created once per session and reused for every call --
    # building one per request would waste time on repeated setup.
    _client: OpenAI = dataclasses.field(init=False, default=None)

    def __post_init__(self):
        """Run automatically right after the dataclass constructor."""
        self._client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        # OpenAI carries the system prompt inside the message list, so seed it
        # as entry zero. It is written once here and then never touched again.
        self._messages.append({"role": "system", "content": self.system_prompt})

    def ask(self, question: str) -> str:
        """
        Say something, and get the reply as plain text.

        This one method performs all three steps from example 02 -- append,
        send, append -- so the caller cannot get the order wrong or skip one.

        Args:
            question: What you want to say, as ordinary text.

        Returns:
            The model's answer, already unwrapped from the response object.
        """
        # Step 1: append the new question to the history.
        self._messages.append({"role": "user", "content": question})

        # Step 2: send the WHOLE history, not just the new question.
        response = self._client.chat.completions.create(
            model=self.model_id,
            messages=self._messages,
        )

        # Step 3: append the reply, so the next `ask()` can see it.
        answer = response.choices[0].message.content
        self._messages.append({"role": "assistant", "content": answer})

        # Unwrap the response once, here, so no caller ever has to.
        return answer


# `__name__ == "__main__"` is true only when this file is run directly, and
# false when it is imported. It keeps the demo below from firing if someone
# later does `from ... import ChatSession` to reuse the class.
if __name__ == "__main__":
    session = ChatSession()

    # The same 3-turn conversation as example 02. Compare this loop with that
    # one: same behaviour, but the dict-wrangling is gone.
    for question in [
        "My favorite number is 7. Just acknowledge it.",
        "Double my favorite number.",
        "What was my favorite number before you doubled it?",
    ]:
        print("\nYou:", question)
        print("AI:", session.ask(question))
