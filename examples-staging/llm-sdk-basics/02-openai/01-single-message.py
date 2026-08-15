# -*- coding: utf-8 -*-

"""
Step 1 of 3 -- Send ONE message to an AI model using the OpenAI SDK.

This is the smallest possible "hello world" for OpenAI: build a request, call
the API, print the answer. There is no agent framework and no helper library
here on purpose -- the whole point is to see the raw shape of what goes over
the wire, because every fancier abstraction is just this with more layers.

What makes OpenAI different from the other three vendors:

- The system prompt is NOT a separate parameter. It is just another message,
  with the role "system", sitting at the front of the list. Bedrock, Claude and
  Gemini all keep it outside the conversation; OpenAI puts it inside.
- `content` is a plain string, not a list of blocks. (It CAN be a list, for
  images and such, but text-only calls take the simple form.)
- Authentication is a single API key -- no region, no cloud account.

- OpenAI Models: https://platform.openai.com/docs/models
- OpenAI Python Example: https://platform.openai.com/docs/api-reference/chat

Requires: uv sync --extra openai   (SDK: openai 2.x)

Credentials: OPENAI_API_KEY in the .env file at the repo root.

Run it:
    .venv/bin/python examples-staging/llm-sdk-basics/02-openai/01-single-message.py
"""

import os

from openai import OpenAI
from dotenv import load_dotenv

# Read the repo-root .env file and copy its keys into os.environ. Without this
# the line below would raise KeyError, because .env is just a text file -- it
# does nothing until some library loads it.
load_dotenv()

# Create the client. It holds your key and the connection settings, and you
# make one and reuse it rather than building a fresh one per request.
#
# Passing api_key is optional -- the SDK reads OPENAI_API_KEY by itself -- but
# being explicit documents exactly which variable this script needs, and turns
# a missing key into an obvious KeyError instead of a confusing 401 later.
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Which model to talk to. Model names are also price tiers: the small/mini
# models cost a fraction of the flagship ones and are plenty for learning.
MODEL_ID = "gpt-5.6-luna"

# The system prompt sets the AI's persona and standing rules. Asking for a short
# answer is not just style: you pay for every token the model generates, so a
# terse instruction is a direct cost control.
SYSTEM_PROMPT = "You are a helpful assistant. Answer in one short sentence."

# The conversation. Even for a single question this must be a LIST, because the
# API has no concept of "one message" -- it always takes a history (you will use
# that fact in example 02).
#
# Each message has exactly two keys:
#   role    -- "system" (standing instructions), "user" (you), or
#              "assistant" (the model).
#   content -- the text itself, as a plain string.
#
# The system message goes FIRST. Order matters: the API reads this list as a
# transcript from top to bottom.
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "Who are you? Please answer in a short sentence."},
]

# Call the API. This is a normal blocking HTTP request: it returns once the
# model has finished generating the whole answer.
#
# We deliberately pass nothing beyond model + messages. The newer models reject
# the old `max_tokens` parameter (they want `max_completion_tokens`) and refuse
# a non-default `temperature`, so the minimal request is the one most likely to
# work on any model you swap in. We keep answers short via the system prompt.
response = client.chat.completions.create(
    model=MODEL_ID,
    messages=messages,
)

# Dig the text out of the response.
#
# `choices` is a LIST because you can ask the API for several alternative
# answers to the same question (the `n` parameter). We asked for one, so we
# take `[0]`. Each choice wraps a message with the same {role, content} shape
# you sent, except role is now "assistant".
answer = response.choices[0].message.content
print("AI:", answer)

# Every response also reports what it cost you. Get in the habit of looking at
# this: `prompt_tokens` covers your system prompt PLUS the whole message
# history, which is why a long conversation gets more expensive every turn.
usage = response.usage
print(f"\nTokens -- in: {usage.prompt_tokens}, out: {usage.completion_tokens}")
