# -*- coding: utf-8 -*-

"""
Send ONE message to a Google Gemini model, with no framework in the way.

Same script as 01 and 02, third vendor. Three spellings of one idea.

Credentials and the model id both come from this project's own config, so
there is nothing to edit here. Put GOOGLE_API_KEY in the repo-root `.env`
and run it.

What makes Google different from the other two:

- Everything that is not the conversation itself goes into one config object:
  the system prompt, the length cap, the temperature.
- For a single question, the conversation can be a bare string. The SDK
  expands it into the full structure for you. A multi-turn history leaves you
  no such shortcut, which is what example 16 builds by hand.
- The reply object has a `.text` shortcut that walks down to the answer for
  you.

Run it:
    .venv/bin/python examples/20-call-the-model-directly/03_gemini.py
"""

from google import genai
from google.genai import types

from agent_app.api import one
from agent_app.constants import DEFAULT_MODEL_ID, LlmProviderEnum

PROVIDER = LlmProviderEnum.GOOGLE.value

api_key = one.config.google_api_key
if not api_key:
    raise SystemExit(
        "GOOGLE_API_KEY is not set. Add it to the .env file at the repo root.\n"
        "See example 04 (get it running) for where to get a key and how to cap "
        "its spend."
    )

MODEL_ID = DEFAULT_MODEL_ID[PROVIDER]

SYSTEM_PROMPT = "You are a helpful assistant. Answer in one short sentence."

QUESTION = "Who are you? Answer in one short sentence."

# The SDK also reads GEMINI_API_KEY on its own. Passing the key explicitly
# removes any doubt about which variable was actually picked up.
client = genai.Client(api_key=api_key)

print(f"Model: {MODEL_ID}")
print("You:", QUESTION)

response = client.models.generate_content(
    model=MODEL_ID,
    # A bare string works for one question. The SDK turns it into a list
    # holding one entry with role="user".
    contents=QUESTION,
    # Every knob other than the conversation lives in this object.
    config=types.GenerateContentConfig(
        # Google's name for the system prompt. Like Anthropic, it sits outside
        # the conversation rather than being a message in it.
        system_instruction=SYSTEM_PROMPT,
        # Hard ceiling on the answer, in tokens. Same safety valve as
        # Anthropic's max_tokens, just optional here.
        max_output_tokens=200,
    ),
)

# `.text` is a convenience shortcut. The long form is
# `response.candidates[0].content.parts[0].text` -- "candidates" is a list
# because the API can return several alternative answers to one question.
answer = response.text
print("AI:", answer)

# Third vendor, third set of field names for the same two numbers.
usage = response.usage_metadata
print(
    f"\nTokens -- in: {usage.prompt_token_count}, "
    f"out: {usage.candidates_token_count}"
)
