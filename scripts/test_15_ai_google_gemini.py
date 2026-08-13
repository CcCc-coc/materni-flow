# -*- coding: utf-8 -*-

"""
Use Google Gemini to ask "Who are you?" to AI.

- Gemini Models: https://ai.google.dev/gemini-api/docs/models
- Gemini Python Example: https://ai.google.dev/gemini-api/docs/quickstart

Requires: uv sync --extra gemini   (SDK: google-genai 1.x)
Credential: GOOGLE_API_KEY in the .env file at the repo root.
"""

import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

# The SDK reads the API key from the environment, so pull .env into it first.
load_dotenv()

# Create Gemini Client
# Pass api_key explicitly: the SDK also looks for GEMINI_API_KEY, and this project
# standardizes on GOOGLE_API_KEY. Being explicit avoids "which one did it pick?".
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

# Prepare message
model_id = "gemini-3.5-flash-lite"  # Use the cheapest model
system_prompt = "You are a helpful AI assistant."
user_message = "Who are you? Please answer in a short sentence."

# Call API
# Note: Gemini takes the prompt as `contents` rather than a messages list, and
# everything else (system prompt, token limit) goes inside a config object.
response = client.models.generate_content(
    model=model_id,
    contents=user_message,
    config=types.GenerateContentConfig(
        system_instruction=system_prompt,
        max_output_tokens=200,
    ),
)

# Extract AI response
# `.text` is a convenience shortcut for the first text part of the first candidate.
ai_response = response.text
print("AI response:", ai_response)

# Print full response
print("\nFull response:", response.model_dump_json(indent=2))
