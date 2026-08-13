# -*- coding: utf-8 -*-

"""
Use OpenAI to ask "Who are you?" to AI.

- OpenAI Models: https://platform.openai.com/docs/models
- OpenAI Python Example: https://platform.openai.com/docs/api-reference/chat

Requires: uv sync --extra openai   (SDK: openai 1.x)
Credential: OPENAI_API_KEY in the .env file at the repo root.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# The SDK reads OPENAI_API_KEY from the environment, so pull .env into it first.
load_dotenv()

# Create OpenAI Client
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Prepare message
model_id = "gpt-5.6-luna"  # Use the cheapest model
system_prompt = "You are a helpful AI assistant."
user_message = "Who are you? Please answer in a short sentence."

# Build request
# Note: unlike Bedrock and Claude, the system prompt is just another message,
# with the role "system", at the front of the list.
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_message},
]

# Call API
# No token limit or temperature is set on purpose: this is only a connectivity
# check, and the newer models reject the older `max_tokens` parameter (they want
# `max_completion_tokens`) as well as a non-default `temperature`. Sending
# nothing extra is the shape most likely to work on any model.
response = client.chat.completions.create(
    model=model_id,
    messages=messages,
)

# Extract AI response
ai_response = response.choices[0].message.content
print("AI response:", ai_response)

# Print full response
print("\nFull response:", response.model_dump_json(indent=2))
