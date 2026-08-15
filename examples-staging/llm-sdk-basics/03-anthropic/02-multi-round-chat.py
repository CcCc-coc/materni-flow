# -*- coding: utf-8 -*-

"""
Step 2 of 3 -- Anthropic Claude. PLACEHOLDER, intentionally not implemented.

This slot is left empty on purpose. The append / send-everything / append-again
loop is identical to the other three vendors -- only the dict shapes differ.

Closest reference: ../01-aws-bedrock/02-multi-round-chat.py

Exercise: fill this in yourself. You will need
    uv sync --extra anthropic
    ANTHROPIC_API_KEY in the .env file at the repo root
and the one thing to watch for is step 3: `response.content` is a list of
BLOCKS, so the assistant entry you append is
    {"role": "assistant", "content": response.content}
not the plain text string.
"""
