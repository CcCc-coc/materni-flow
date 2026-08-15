# -*- coding: utf-8 -*-

"""
Step 3 of 3 -- Hide the bookkeeping behind a small ChatSession class.

Example 02 works, but look at what the caller had to remember: build the right
dict shape, append before the call, append again after the call, then reach
through four levels of nested keys to find the text. That is a lot of ceremony
for "ask a question", and every place in your app that wants to chat has to
repeat all of it -- and can forget a step.

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

Requires: nothing extra -- boto3 is already a core dependency of this project.

Credentials: AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, or any other
credential source boto3 already knows about (e.g. `~/.aws/credentials`).

Run it:
    .venv/bin/python examples-staging/llm-sdk-basics/01-aws-bedrock/03-chat-session-class.py
"""

import os
import dataclasses
import typing as T

import boto3
from dotenv import load_dotenv

# See 01-single-message.py for why we do not put AWS keys in .env.
load_dotenv()

MODEL_ID = "us.amazon.nova-micro-v1:0"
SYSTEM_PROMPT = "You are a helpful assistant. Answer in one short sentence."


@dataclasses.dataclass
class ChatSession:
    """
    One ongoing conversation with a Bedrock model.

    One instance == one conversation. Create a second instance and it starts
    from a blank history, with no knowledge of the first -- which is exactly
    how you would serve two different users at the same time.

    Attributes:
        model_id: Which Bedrock model to talk to.
        system_prompt: The standing instruction sent on every single call.
            It is stored once here rather than passed on every `ask()`, because
            it never changes during a conversation.
        max_tokens: Ceiling on the length of each answer.
        temperature: Randomness of the output, 0.0 (repeatable) to 1.0 (creative).
    """

    model_id: str = MODEL_ID
    system_prompt: str = SYSTEM_PROMPT
    max_tokens: int = 100
    temperature: float = 0.7

    # The conversation history, identical in content to the `messages` list you
    # managed by hand in example 02 -- it has just moved inside the object.
    #
    # `init=False` keeps it out of the constructor: it is internal state, not
    # something a caller supplies. `default_factory=list` gives each instance
    # its OWN empty list. (Writing `_messages: list = []` would be a classic
    # Python bug: every instance would share one list and every conversation
    # would bleed into every other.)
    _messages: list[dict] = dataclasses.field(init=False, default_factory=list)

    # The boto3 client, created once per session and reused for every call --
    # building one per request would waste time on repeated setup.
    #
    # The type is loose (`T.Any`) on purpose: boto3 builds its service classes
    # at runtime, so there is no real class to name here.
    _client: T.Any = dataclasses.field(init=False, default=None)

    def __post_init__(self):
        """Run automatically right after the dataclass constructor."""
        session = boto3.Session(region_name=os.environ.get("AWS_REGION", "us-east-1"))
        self._client = session.client("bedrock-runtime")

    def ask(self, question: str) -> str:
        """
        Say something, and get the reply as plain text.

        This one method performs all three steps from example 02 -- append,
        send, append -- so the caller cannot get the order wrong or skip one.

        Args:
            question: What you want to say, as ordinary text.

        Returns:
            The model's answer, already unwrapped from the nested response.
        """
        # Step 1: append the new question to the history.
        self._messages.append(
            {
                "role": "user",
                "content": [{"text": question}],
            }
        )

        # Step 2: send the WHOLE history, not just the new question.
        response = self._client.converse(
            modelId=self.model_id,
            messages=self._messages,
            system=[{"text": self.system_prompt}],
            inferenceConfig={
                "maxTokens": self.max_tokens,
                "temperature": self.temperature,
            },
        )

        # Step 3: append the reply, so the next `ask()` can see it.
        reply = response["output"]["message"]
        self._messages.append(reply)

        # Unwrap the nested response once, here, so no caller ever has to.
        return reply["content"][0]["text"]


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
