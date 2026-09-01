# -*- coding: utf-8 -*-

"""
Send ONE message to an OpenAI model, with no framework in the way.

This is the smallest thing that can be called an AI application: build a
request, call the API, print the answer. No agent, no tools, no streaming --
every fancier abstraction in this repo is this, with more layers on top.

Credentials and the model id both come from this project's own config, so
there is nothing to edit here. Put OPENAI_API_KEY in the repo-root `.env`
and run it.

What makes OpenAI different from the other two:

- The system prompt is NOT a separate parameter. It is just another message,
  with the role "system", sitting at the front of the list. Anthropic and
  Google both keep it outside the conversation; OpenAI puts it inside.
- `content` is a plain string. (It can be a list of blocks for images and
  such, but a text-only call takes the simple form.)

Run it:
    .venv/bin/python examples/15-call-the-model-directly/01_openai.py
"""

from openai import OpenAI

# `one` is this project's single assembly point. Importing it is free: nothing
# connects, nothing is read, until you touch an attribute. `one.config` is the
# first thing this app builds, and it has already loaded `.env` for us.
from agent_app.api import one
from agent_app.constants import DEFAULT_MODEL_ID, LlmProviderEnum

PROVIDER = LlmProviderEnum.OPENAI.value

# The key, straight out of the config this whole app already uses. Reading it
# here rather than from os.environ means this script and the running app can
# never disagree about where credentials come from.
api_key = one.config.openai_api_key
if not api_key:
    raise SystemExit(
        "OPENAI_API_KEY is not set. Add it to the .env file at the repo root.\n"
        "See example 04 (get it running) for where to get a key and how to cap "
        "its spend."
    )

# The provider's default model, from the same table the app uses. Note this is
# NOT `one.config.model_id`: that one follows LLM_PROVIDER, and this script is
# about OpenAI whichever provider the app happens to be pointed at.
MODEL_ID = DEFAULT_MODEL_ID[PROVIDER]

# The system prompt sets the model's persona and standing rules. Asking for a
# short answer is a direct cost control, not a style choice: you pay for every
# token generated.
SYSTEM_PROMPT = "You are a helpful assistant. Answer in one short sentence."

# Create the client once and reuse it. It holds the key and the connection
# settings; building a fresh one per request wastes setup time.
client = OpenAI(api_key=api_key)

# The conversation. Even for a single question this is a LIST, because the API
# has no concept of "one message" -- it always takes a transcript, read top to
# bottom. The system message goes first.
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "Who are you? Answer in one short sentence."},
]

print(f"Model: {MODEL_ID}")
print("You:", messages[-1]["content"])

# A normal blocking HTTP request. It returns once the model has finished
# generating the whole answer.
#
# Nothing is passed beyond model + messages on purpose. Newer models reject the
# older length parameter and refuse a non-default temperature, so the minimal
# request is the one most likely to work whichever model you swap in.
response = client.chat.completions.create(
    model=MODEL_ID,
    messages=messages,
)

# `choices` is a list because the API can return several alternative answers to
# one question. We asked for one, so take the first. Each choice wraps a message
# with the same {role, content} shape you sent, except role is now "assistant".
answer = response.choices[0].message.content
print("AI:", answer)

# Every response reports what it cost. Get in the habit of reading this:
# `prompt_tokens` covers the system prompt PLUS the whole history, which is why
# a long conversation gets more expensive every single turn.
usage = response.usage
print(f"\nTokens -- in: {usage.prompt_tokens}, out: {usage.completion_tokens}")
