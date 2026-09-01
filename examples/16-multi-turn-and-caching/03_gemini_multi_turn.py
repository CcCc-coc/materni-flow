# -*- coding: utf-8 -*-

"""
Three turns of conversation with a Google Gemini model, history by hand.

Same three steps again. Two things differ: the system prompt lives in the
config object, and the history is built out of typed objects rather than plain
dicts.

Google's SDK also ships a `client.chats` helper that keeps the history for you.
It is deliberately NOT used here -- the point of this script is to see the
mechanism, and a helper hides exactly the part worth seeing.

Run it:
    .venv/bin/python examples/16-multi-turn-and-caching/03_gemini_multi_turn.py
"""

from google import genai
from google.genai import types

from agent_app.api import one
from agent_app.constants import DEFAULT_MODEL_ID, LlmProviderEnum

api_key = one.config.google_api_key
if not api_key:
    raise SystemExit("GOOGLE_API_KEY is not set. Add it to the .env file at the repo root.")

MODEL_ID = DEFAULT_MODEL_ID[LlmProviderEnum.GOOGLE.value]
SYSTEM_PROMPT = "You are a helpful assistant. Answer in one short sentence."

QUESTIONS = [
    "My favorite number is 7. Just acknowledge it.",
    "Double my favorite number.",
    "What was my favorite number before you doubled it?",
]

client = genai.Client(api_key=api_key)

# Same as Anthropic: the history holds only the back and forth. The system
# prompt goes in the config object on every call.
#
# Note the role for the model's turn is "model", not "assistant". Third vendor,
# third vocabulary for the same idea.
contents = []

for i, question in enumerate(QUESTIONS, start=1):
    print(f"\n===== Turn {i} =====")
    print("You:", question)

    # Step 1: append the question, as a typed Content object.
    contents.append(
        types.Content(role="user", parts=[types.Part(text=question)])
    )

    # Step 2: send the whole history.
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=200,
        ),
    )

    # Step 3: append the reply.
    answer = response.text
    contents.append(
        types.Content(role="model", parts=[types.Part(text=answer)])
    )

    print("AI:", answer)

    usage = response.usage_metadata
    print(
        f"Tokens -- in: {usage.prompt_token_count}, "
        f"out: {usage.candidates_token_count}"
    )

print(f"\n===== Done: history holds {len(contents)} entries =====")
print("3 questions + 3 answers = 6. The system instruction is not in here.")
