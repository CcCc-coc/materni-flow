# -*- coding: utf-8 -*-

"""
Watch prompt caching happen: the same long prompt, sent twice.

Script 01 showed the input token count climbing every turn, because the whole
history is re-sent each time. Prompt caching is the vendors' answer to that:
the parts of your request that did not change can be served from a cache at a
fraction of the price.

This script sends one deliberately long system prompt twice and prints the
cache counters, so you can see the second call land on the cache.

Why OpenAI for this demo: its caching is automatic. There is no extra parameter
to set, which keeps the script about the IDEA rather than about one vendor's
syntax. The other two work differently:

- Anthropic: explicit. You mark a content block with a cache control field, and
  the counters come back as cache_creation_input_tokens / cache_read_input_tokens.
- Google: has both an implicit cache and an explicit one you create up front.

The concept is the same everywhere, and so is the rule that matters most:
THE CACHED PART MUST COME FIRST AND MUST NOT CHANGE. Caching works on a prefix.
Change one character near the top and everything after it is a miss.

Run it:
    .venv/bin/python examples/21-multi-turn-and-caching/05_prompt_caching.py
"""

from openai import OpenAI

from agent_app.api import one
from agent_app.constants import DEFAULT_MODEL_ID, LlmProviderEnum

api_key = one.config.openai_api_key
if not api_key:
    raise SystemExit("OPENAI_API_KEY is not set. Add it to the .env file at the repo root.")

MODEL_ID = DEFAULT_MODEL_ID[LlmProviderEnum.OPENAI.value]

# Caching only kicks in above a minimum size -- roughly a thousand tokens for
# most vendors and models. Below it, caching is SILENTLY disabled: no error, no
# warning, the counters simply stay at zero.
#
# So this prompt is padded on purpose. In a real app the thing that fills this
# space is your actual standing context: the domain rules, the database schema,
# the worked examples. In this repo that is `data/system-prompt.md`, which is
# several thousand tokens and is re-sent on every single request.
LONG_SYSTEM_PROMPT = (
    "You are an analyst for a small business lender. "
    "Answer in one short sentence. "
) * 200

client = OpenAI(api_key=api_key)

messages = [
    {"role": "system", "content": LONG_SYSTEM_PROMPT},
    {"role": "user", "content": "Say OK."},
]


def report(label: str, usage) -> None:
    """Print the cache counters, tolerating a vendor renaming a field."""
    details = getattr(usage, "prompt_tokens_details", None)
    written = getattr(details, "cache_write_tokens", None)
    read = getattr(details, "cached_tokens", None)

    print(f"\n--- {label} ---")
    print(f"input tokens:  {usage.prompt_tokens}")
    print(f"output tokens: {usage.completion_tokens}")
    if details is None:
        print("no cache detail on this response -- check the vendor's docs for")
        print("the current field name, or the model may not support caching")
        return
    print(f"written to cache: {written}")
    print(f"read from cache:  {read}")


print(f"Model: {MODEL_ID}")
print(f"System prompt: {len(LONG_SYSTEM_PROMPT)} characters. The real token count is in")
print("the report below -- characters are not tokens, and the ratio varies.")

# First call: nothing is in the cache yet, so the prompt gets written INTO it.
# You pay normal price for this one.
first = client.chat.completions.create(model=MODEL_ID, messages=messages)
report("call 1", first.usage)

# Second call: byte-for-byte the same prefix, so it is served FROM the cache at
# a fraction of the price. Note the input token count does not drop -- you are
# still sending the same thing. What changes is what it costs.
second = client.chat.completions.create(model=MODEL_ID, messages=messages)
report("call 2", second.usage)

print("\n===== What to notice =====")
print("1. Input token count is IDENTICAL on both calls. Caching does not make")
print("   the request smaller, it makes the same request cheaper.")
print("2. Call 1 writes, call 2 reads. The saving is on the read.")
print("3. Change one character near the TOP of the prompt and call 2 becomes a")
print("   miss again, because caching matches a prefix.")
