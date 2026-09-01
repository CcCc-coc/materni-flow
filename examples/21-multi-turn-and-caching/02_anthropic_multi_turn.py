# -*- coding: utf-8 -*-

"""
Three turns of conversation with an Anthropic Claude model, history by hand.

Same three steps as the OpenAI script: append the question, send the whole
history, append the reply. The one structural difference is where the system
prompt lives.

Run it:
    .venv/bin/python examples/21-multi-turn-and-caching/02_anthropic_multi_turn.py
"""

import anthropic

from agent_app.api import one
from agent_app.constants import DEFAULT_MODEL_ID, LlmProviderEnum

api_key = one.config.anthropic_api_key
if not api_key:
    raise SystemExit("ANTHROPIC_API_KEY is not set. Add it to the .env file at the repo root.")

MODEL_ID = DEFAULT_MODEL_ID[LlmProviderEnum.ANTHROPIC.value]
SYSTEM_PROMPT = "You are a helpful assistant. Answer in one short sentence."

QUESTIONS = [
    "My favorite number is 7. Just acknowledge it.",
    "Double my favorite number.",
    "What was my favorite number before you doubled it?",
]

client = anthropic.Anthropic(api_key=api_key)

# The history starts EMPTY here, unlike the OpenAI version. The system prompt
# is not a message for this vendor -- it goes in as its own parameter on every
# call, which you can see in the request below.
messages = []

for i, question in enumerate(QUESTIONS, start=1):
    print(f"\n===== Turn {i} =====")
    print("You:", question)

    # Step 1: append the question.
    messages.append({"role": "user", "content": question})

    # Step 2: send the whole history, plus the system prompt as a separate
    # argument. Note it is re-sent on every call too -- it is not remembered
    # any more than the messages are.
    response = client.messages.create(
        model=MODEL_ID,
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    # Step 3: append the reply.
    #
    # The reply arrives as a list of content blocks, so unwrap the first one's
    # text. The history entry is stored as a plain string, which this API
    # accepts for an assistant turn.
    answer = response.content[0].text
    messages.append({"role": "assistant", "content": answer})

    print("AI:", answer)

    usage = response.usage
    print(f"Tokens -- in: {usage.input_tokens}, out: {usage.output_tokens}")

print(f"\n===== Done: history holds {len(messages)} messages =====")
print("3 questions + 3 answers = 6. The system prompt is not in here.")
