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
    3. append the model's reply back into it        (role="model")

Miss step 3 and the model develops amnesia -- it will never see its own
previous answers, so it cannot follow up on them.

Two Gemini-specific notes:

- The reply's role is "model", not "assistant". Every other vendor in this
  folder calls it "assistant"; Gemini does not, and sending the wrong word is
  a validation error.
- The bare-string shortcut from example 01 is gone. Once there is a history,
  `contents` must be a real list of typed `types.Content` objects.
- The SDK does ship a built-in helper for exactly this (`client.chats`), which
  we skip on purpose: the whole point of this file is to do the bookkeeping
  yourself once, so you know what such a helper is doing for you.

Cost warning: because every turn resends everything before it, input tokens grow
quadratically over a long chat. Watch the token counts printed at the end.

Requires: uv sync --extra gemini   (SDK: google-genai 1.x)

Credentials: GOOGLE_API_KEY in the .env file at the repo root.

Run it:
    .venv/bin/python examples-staging/llm-sdk-basics/04-google-gemini/02-multi-round-chat.py
"""

import os

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

MODEL_ID = "gemini-3.5-flash-lite"
SYSTEM_PROMPT = "You are a helpful assistant. Answer in one short sentence."

# The three things we will say, in order. Read them as a test: the third one is
# unanswerable unless the model can still see the first.
QUESTIONS = [
    "My favorite number is 7. Just acknowledge it.",
    "Double my favorite number.",
    "What was my favorite number before you doubled it?",
]

# THE conversation history. This list is the entire "memory" of the chat -- it
# lives here in your Python process, not on Google's servers. It starts empty
# and grows by two entries per turn (your message, then the model's reply).
#
# The system prompt is NOT in here: it goes in the config object, sent fresh on
# every call.
contents = []

for i, question in enumerate(QUESTIONS, start=1):
    print(f"\n===== Turn {i} =====")
    print("You:", question)

    # --- Step 1: append what you are about to say -------------------------
    # Note we APPEND rather than replace. Everything said earlier stays.
    #
    # `Content` is one turn of the conversation, and `parts` is a list because
    # one turn can carry several pieces at once: text, an image, a file. Here
    # we send a single text part.
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part(text=question)],
        )
    )

    # --- Step 2: send the whole history ----------------------------------
    # `contents` is the full transcript, not just the new question. On turn 3
    # this list already holds 5 entries and all 5 get uploaded again.
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=100,
            temperature=0.7,
        ),
    )

    # --- Step 3: append the reply back into the history -------------------
    # This is the step beginners forget. Conveniently, the object at
    # response.candidates[0].content is already a `Content` with role="model",
    # so it drops straight into the list with no conversion.
    reply = response.candidates[0].content
    contents.append(reply)

    print("AI:", response.text)

    # Watch `prompt_token_count` climb on every turn even though your questions
    # stay the same length. That growth IS the resent history -- it is the price
    # of memory, and it is why production apps eventually trim or summarize old
    # turns instead of keeping everything forever.
    usage = response.usage_metadata
    print(
        f"Tokens -- in: {usage.prompt_token_count}, "
        f"out: {usage.candidates_token_count}"
    )

# The finished transcript: 3 questions + 3 answers = 6 entries. Notice that it
# is nothing but a plain Python list. There is no magic here, which is exactly
# what makes step 3 easy to wrap in a class -- see 03-chat-session-class.py.
print(f"\n===== Done: history holds {len(contents)} messages =====")
