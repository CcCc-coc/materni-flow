# -*- coding: utf-8 -*-

"""
Step 1 of 3 -- Anthropic Claude. PLACEHOLDER, intentionally not implemented.

This slot is left empty on purpose. The Claude API is shaped almost exactly
like Bedrock's (system prompt as its own top-level parameter, `content` as a
list of blocks), so writing it out a fourth time would teach nothing new.

Closest reference: ../01-aws-bedrock/01-single-message.py

Exercise: fill this in yourself. You will need
    uv sync --extra anthropic
    ANTHROPIC_API_KEY in the .env file at the repo root
and the two differences that trip people up are that `max_tokens` is REQUIRED
by this API, and the call is `client.messages.create(...)`.
"""
