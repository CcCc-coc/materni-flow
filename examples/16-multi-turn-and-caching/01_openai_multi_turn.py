# -*- coding: utf-8 -*-

"""
Three turns of conversation with an OpenAI model, history managed by hand.

The model remembers NOTHING between calls. What makes a conversation feel like
a conversation is that you resend the whole transcript every single time. This
script does that by hand so the mechanism is visible.

Read the three questions below as a test: the third one is unanswerable unless
the model can still see the first.

Credentials and the model id come from this project's config, so there is
nothing to edit here.

Run it:
    .venv/bin/python examples/16-multi-turn-and-caching/01_openai_multi_turn.py
"""

from openai import OpenAI

from agent_app.api import one
from agent_app.constants import DEFAULT_MODEL_ID, LlmProviderEnum

api_key = one.config.openai_api_key
if not api_key:
    raise SystemExit("OPENAI_API_KEY is not set. Add it to the .env file at the repo root.")

MODEL_ID = DEFAULT_MODEL_ID[LlmProviderEnum.OPENAI.value]
SYSTEM_PROMPT = "You are a helpful assistant. Answer in one short sentence."

QUESTIONS = [
    "My favorite number is 7. Just acknowledge it.",
    "Double my favorite number.",
    "What was my favorite number before you doubled it?",
]

client = OpenAI(api_key=api_key)

# THE conversation history. This list is the entire memory of the chat, and it
# lives here in your Python process -- not on OpenAI's servers.
#
# Unlike the other two vendors it does not start empty: OpenAI carries the
# system prompt inside the message list, so it is seeded as entry zero and then
# never touched again.
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
]

for i, question in enumerate(QUESTIONS, start=1):
    print(f"\n===== Turn {i} =====")
    print("You:", question)

    # Step 1: APPEND the new question. Everything said earlier stays.
    messages.append({"role": "user", "content": question})

    # Step 2: send the WHOLE history, not just the new question. On turn 3 this
    # list already holds 6 entries, and all 6 go up again.
    response = client.chat.completions.create(model=MODEL_ID, messages=messages)

    # Step 3: append the reply back into the history.
    #
    # This is the step beginners forget, and forgetting it is invisible on turn
    # 1 and 2 -- it only shows up as the model losing the thread later.
    answer = response.choices[0].message.content
    messages.append({"role": "assistant", "content": answer})

    print("AI:", answer)

    # Watch `prompt_tokens` climb every turn even though your questions stay the
    # same length. That growth IS the resent history. It is the price of memory.
    usage = response.usage
    print(f"Tokens -- in: {usage.prompt_tokens}, out: {usage.completion_tokens}")

print(f"\n===== Done: history holds {len(messages)} messages =====")
print("1 system + 3 questions + 3 answers = 7. Nothing but a list of dicts.")
