# -*- coding: utf-8 -*-

"""
Step 1 of 3 -- Send ONE message to an AI model using the Google Gemini SDK.

This is the smallest possible "hello world" for Gemini: build a request, call
the API, print the answer. There is no agent framework and no helper library
here on purpose -- the whole point is to see the raw shape of what goes over
the wire, because every fancier abstraction is just this with more layers.

What makes Gemini different from the other three vendors:

- The parameter is called `contents`, not `messages`, and for a single question
  you may hand it a bare string -- no list, no dict, no role. It is the least
  ceremonious of the four APIs for this one case.
- Everything that is not the conversation (system prompt, token limit,
  temperature) goes inside one `config` object rather than being a top-level
  argument.
- The model's role is called "model", NOT "assistant". This matters the moment
  you build a history by hand -- see example 02.

- Gemini Models: https://ai.google.dev/gemini-api/docs/models
- Gemini Python Example: https://ai.google.dev/gemini-api/docs/quickstart

Requires: uv sync --extra gemini   (SDK: google-genai 1.x)

Credentials: GOOGLE_API_KEY in the .env file at the repo root.

Run it:
    .venv/bin/python examples-staging/llm-sdk-basics/04-google-gemini/01-single-message.py
"""

import os

from google import genai
from google.genai import types
from dotenv import load_dotenv

# Read the repo-root .env file and copy its keys into os.environ. Without this
# the line below would raise KeyError, because .env is just a text file -- it
# does nothing until some library loads it.
load_dotenv()

# Create the client. It holds your key and the connection settings, and you
# make one and reuse it rather than building a fresh one per request.
#
# Pass api_key explicitly here. The SDK also accepts GEMINI_API_KEY, and this
# project standardizes on GOOGLE_API_KEY -- being explicit removes any doubt
# about which variable was actually picked up.
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

# Which model to talk to. Model names are also price tiers: the flash/lite
# models cost a fraction of the pro ones and are plenty for learning.
MODEL_ID = "gemini-3.5-flash-lite"

# The system prompt sets the AI's persona and standing rules. Asking for a short
# answer is not just style: you pay for every token the model generates, so a
# terse instruction is a direct cost control.
SYSTEM_PROMPT = "You are a helpful assistant. Answer in one short sentence."

# Call the API. This is a normal blocking HTTP request: it returns once the
# model has finished generating the whole answer.
response = client.models.generate_content(
    model=MODEL_ID,
    # For a single question, `contents` accepts a bare string. The SDK expands
    # it into the full structure for you: a list holding one Content with
    # role="user". Example 02 builds that structure by hand, because a
    # multi-turn history leaves you no shortcut.
    contents="Who are you? Please answer in a short sentence.",
    # Every knob other than the conversation itself lives in this config object.
    config=types.GenerateContentConfig(
        # Gemini's name for the system prompt. Note it is NOT a message with a
        # role -- like Bedrock and Claude, it sits outside the conversation.
        system_instruction=SYSTEM_PROMPT,
        # Hard ceiling on the ANSWER length, counted in tokens (roughly 3/4 of
        # a word each). This is a safety valve against a runaway bill -- if the
        # model hits the limit it simply stops mid-sentence.
        max_output_tokens=100,
        # How random the output is. Low values make the model pick the most
        # likely next word almost every time, so answers are repeatable; high
        # values make it more creative and less predictable.
        temperature=0.7,
    ),
)

# Dig the text out of the response.
#
# `.text` is a convenience shortcut the SDK provides: it walks down to the first
# candidate and joins its text parts. The long form is
# `response.candidates[0].content.parts[0].text` -- "candidates" is a list
# because the API can return several alternative answers to one question.
answer = response.text
print("AI:", answer)

# Every response also reports what it cost you. Get in the habit of looking at
# this: `prompt_token_count` covers your system prompt PLUS the whole message
# history, which is why a long conversation gets more expensive every turn.
usage = response.usage_metadata
print(
    f"\nTokens -- in: {usage.prompt_token_count}, "
    f"out: {usage.candidates_token_count}"
)
