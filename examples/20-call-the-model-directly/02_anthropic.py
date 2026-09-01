# -*- coding: utf-8 -*-

"""
Send ONE message to an Anthropic Claude model, with no framework in the way.

Same script as 01, different vendor. Read them side by side: what stays the
same is the shape of the problem, what changes is the vendor's spelling of it.

Credentials and the model id both come from this project's own config, so
there is nothing to edit here. Put ANTHROPIC_API_KEY in the repo-root `.env`
and run it.

What makes Anthropic different from OpenAI:

- The system prompt is its OWN top-level parameter, not a message. The message
  list holds only the back and forth between user and assistant.
- `max_tokens` is REQUIRED. OpenAI and Google will happily run without it;
  this API refuses the call.
- The answer comes back as a list of content blocks, not a plain string, so
  you index into it to get the text.

Run it:
    .venv/bin/python examples/20-call-the-model-directly/02_anthropic.py
"""

import anthropic

from agent_app.api import one
from agent_app.constants import DEFAULT_MODEL_ID, LlmProviderEnum

PROVIDER = LlmProviderEnum.ANTHROPIC.value

api_key = one.config.anthropic_api_key
if not api_key:
    raise SystemExit(
        "ANTHROPIC_API_KEY is not set. Add it to the .env file at the repo root.\n"
        "See example 04 (get it running) for where to get a key and how to cap "
        "its spend."
    )

MODEL_ID = DEFAULT_MODEL_ID[PROVIDER]

SYSTEM_PROMPT = "You are a helpful assistant. Answer in one short sentence."

client = anthropic.Anthropic(api_key=api_key)

# Only the conversation goes in here. The system prompt is passed separately
# below -- that is the one structural difference from the OpenAI script.
messages = [
    {"role": "user", "content": "Who are you? Answer in one short sentence."},
]

print(f"Model: {MODEL_ID}")
print("You:", messages[-1]["content"])

response = client.messages.create(
    model=MODEL_ID,
    # Required by this API. It is a hard ceiling on the ANSWER, counted in
    # tokens, and it is also your last line of defence against a runaway bill:
    # if the model hits it, generation simply stops.
    max_tokens=200,
    # The system prompt as its own parameter, outside the conversation.
    system=SYSTEM_PROMPT,
    messages=messages,
)

# The reply is a list of content blocks. A text-only answer is one block of
# type "text", so take the first one's `.text`. The list exists because a reply
# can also carry tool calls and other block types.
answer = response.content[0].text
print("AI:", answer)

# Same habit as before. Note the field names differ from OpenAI's -- every
# vendor spells this differently, which is exactly why the app wraps them.
usage = response.usage
print(f"\nTokens -- in: {usage.input_tokens}, out: {usage.output_tokens}")
