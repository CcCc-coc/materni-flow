# -*- coding: utf-8 -*-

"""
Step 2 of 3 -- Hold a 3-turn conversation by managing the history by hand.

Here is the single most surprising fact about every LLM API on the market:

    The model has NO memory. Each API call is completely independent.

There is no session on the server, nothing is stored between calls, and the
model cannot recall what it told you a second ago. What creates the illusion of
memory is that YOU resend the entire conversation every single time. Turn 3
works only because the request carries turns 1 and 2 inside it.

So the loop you must run yourself is:

    1. append your new question to the history      (role="user")
    2. send the WHOLE history
    3. append the model's reply back into it        (role="assistant")

Miss step 3 and the model develops amnesia -- it will never see its own
previous answers, so it cannot follow up on them.

The conversation below is built to prove the memory is real: the last question
can only be answered from turn 1, which by then is ancient history.

Cost warning: because every turn resends everything before it, input tokens grow
quadratically over a long chat. Watch the token counts printed at the end.

Requires: uv sync --extra openai   (SDK: openai 2.x)

Credentials: OPENAI_API_KEY in the .env file at the repo root.

Run it:
    .venv/bin/python examples-staging/llm-sdk-basics/02-openai/02-multi-round-chat.py
"""

import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

MODEL_ID = "gpt-5.6-luna"
SYSTEM_PROMPT = "You are a helpful assistant. Answer in one short sentence."

# The three things we will say, in order. Read them as a test: the third one is
# unanswerable unless the model can still see the first.
QUESTIONS = [
    "My favorite number is 7. Just acknowledge it.",
    "Double my favorite number.",
    "What was my favorite number before you doubled it?",
]

# THE conversation history. This list is the entire "memory" of the chat -- it
# lives here in your Python process, not on OpenAI's servers.
#
# Unlike the other vendors, it does not start empty: OpenAI carries the system
# prompt inside the message list, so it is seeded here as entry zero and then
# simply never touched again.
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
]

for i, question in enumerate(QUESTIONS, start=1):
    print(f"\n===== Turn {i} =====")
    print("You:", question)

    # --- Step 1: append what you are about to say -------------------------
    # Note we APPEND rather than replace. Everything said earlier stays.
    messages.append({"role": "user", "content": question})

    # --- Step 2: send the whole history ----------------------------------
    # `messages` is the full transcript, not just the new question. On turn 3
    # this list already holds 6 entries and all 6 get uploaded again.
    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=messages,
    )

    # --- Step 3: append the reply back into the history -------------------
    # This is the step beginners forget.
    #
    # Note the small conversion: the SDK hands back a typed object, but the
    # history is a list of plain dicts, so we rebuild the reply as a dict. (You
    # may also append `response.choices[0].message` directly -- the SDK accepts
    # its own objects -- but keeping the list uniformly dict-shaped makes it
    # trivial to save to JSON or a database later.)
    answer = response.choices[0].message.content
    messages.append({"role": "assistant", "content": answer})

    print("AI:", answer)

    # Watch `prompt_tokens` climb on every turn even though your questions stay
    # the same length. That growth IS the resent history -- it is the price of
    # memory, and it is why production apps eventually trim or summarize old
    # turns instead of keeping everything forever.
    usage = response.usage
    print(f"Tokens -- in: {usage.prompt_tokens}, out: {usage.completion_tokens}")

# The finished transcript: 1 system + 3 questions + 3 answers = 7 entries.
# Notice that it is nothing but a plain Python list of plain dicts. There is no
# magic here, which is exactly what makes step 3 easy to wrap in a class -- see
# 03-chat-session-class.py.
print(f"\n===== Done: history holds {len(messages)} messages =====")
