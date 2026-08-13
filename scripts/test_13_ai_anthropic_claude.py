# -*- coding: utf-8 -*-

"""
Use Anthropic Claude to ask "Who are you?" to AI.

- Claude Models: https://platform.claude.com/docs/en/about-claude/models/overview
- Claude Python Example: https://platform.claude.com/docs/en/api/client-sdks

Requires: uv sync --extra anthropic   (SDK: anthropic 0.x)
Credential: ANTHROPIC_API_KEY in the .env file at the repo root.
"""

import os
import anthropic
from dotenv import load_dotenv

# The SDK reads ANTHROPIC_API_KEY from the environment, so pull .env into it first.
load_dotenv()

# Create Anthropic Client
# Passing api_key explicitly is not required (the SDK finds it on its own), but it
# makes it obvious which environment variable this script needs.
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# Prepare message
model_id = "claude-haiku-4-5-20251001"  # Use the cheapest model
system_prompt = "You are a helpful AI assistant."
user_message = "Who are you? Please answer in a short sentence."

# Build request
# Note: unlike OpenAI, the system prompt is NOT a message. It is its own
# top-level parameter, the same way Bedrock keeps it separate from `messages`.
messages = [
    {
        "role": "user",
        "content": user_message,
    }
]

# Call API
response = client.messages.create(
    model=model_id,
    max_tokens=200,  # required by this API, unlike OpenAI and Gemini
    system=system_prompt,
    messages=messages,
)

# Extract AI response
# `content` is a LIST of blocks (text, tool_use, thinking, ...), not a string.
ai_response = response.content[0].text
print("AI response:", ai_response)

# Print full response
print("\nFull response:", response.model_dump_json(indent=2))
