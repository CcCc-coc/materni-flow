# -*- coding: utf-8 -*-

"""
Step 1 of 3 -- Send ONE message to an AI model using the AWS Bedrock SDK.

This is the smallest possible "hello world" for Bedrock: build a request, call
the API, print the answer. There is no agent framework and no helper library
here on purpose -- the whole point is to see the raw shape of what goes over
the wire, because every fancier abstraction is just this with more layers.

What makes Bedrock different from the other three vendors:

- There is no API key. Bedrock authenticates with ordinary AWS credentials --
  the same ones the `aws` CLI uses -- and it always needs a region, because
  models are hosted per-region.
- One API call (`converse`) covers every model Bedrock hosts: Amazon's own
  Nova, Anthropic's Claude, Meta's Llama. You switch models by changing one
  string, and the request/response shape stays identical.

Requires: nothing extra -- boto3 is already a core dependency of this project.

Credentials: AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, or any other
credential source boto3 already knows about (e.g. `~/.aws/credentials`).

Run it:
    .venv/bin/python examples-staging/llm-sdk-basics/01-aws-bedrock/01-single-message.py
"""

import os

import boto3
from dotenv import load_dotenv

# Load the repo-root .env into os.environ so AWS_REGION below can be read from it.
#
# GOTCHA, specific to AWS: boto3 checks environment variables BEFORE it reads
# ~/.aws/credentials. So if your .env contains a placeholder like
# AWS_ACCESS_KEY_ID=your-key-here, that fake value wins over the real profile on
# your machine and every call fails with an auth error. If you already have a
# working AWS profile, leave the two key variables out of .env entirely.
load_dotenv()

# Create the Bedrock client.
#
# A boto3 "session" holds credentials + region; a "client" is the typed caller
# for one specific AWS service. We ask for "bedrock-runtime" (the service that
# RUNS models) rather than "bedrock" (the service that manages/lists them) --
# two different services, easy to mix up.
#
# Note we do NOT pass aws_access_key_id / aws_secret_access_key. Leaving them
# out lets boto3 search all its usual places in order: environment variables,
# ~/.aws/credentials, then the IAM role attached to the machine. That is what
# you want, because the exact same code then works locally and in production.
session = boto3.Session(region_name=os.environ.get("AWS_REGION", "us-east-1"))
bedrock = session.client("bedrock-runtime")

# The model to talk to. Nova Micro is Amazon's cheapest model, which is all we
# need to prove the plumbing works. The "us." prefix means it is a cross-region
# inference profile: AWS may serve the request from any US region that has
# spare capacity. The ":0" on the end is the model version.
MODEL_ID = "us.amazon.nova-micro-v1:0"

# The system prompt sets the AI's persona and standing rules. It is NOT part of
# the conversation -- the user never "said" it. Asking for a short answer here
# is not just style: you pay for every token the model generates, so a terse
# instruction is a direct cost control.
SYSTEM_PROMPT = "You are a helpful assistant. Answer in one short sentence."

# The conversation so far. Even for a single question this must be a LIST,
# because the API has no concept of "one message" -- it always takes a history
# (you will use that fact in example 02).
#
# Each message has exactly two keys:
#   role    -- "user" (you) or "assistant" (the model). Nothing else is valid.
#   content -- a LIST of content blocks, NOT a plain string. It is a list
#              because one message can carry several things at once: text, an
#              image, a document. Here we send a single text block.
messages = [
    {
        "role": "user",
        "content": [
            {"text": "Who are you? Please answer in a short sentence."},
        ],
    },
]

# Call the API. This is a normal blocking HTTP request: it returns once the
# model has finished generating the whole answer.
response = bedrock.converse(
    modelId=MODEL_ID,
    messages=messages,
    # The system prompt is its own top-level parameter, kept OUTSIDE `messages`.
    # It is also a list of blocks, for the same reason `content` is.
    system=[{"text": SYSTEM_PROMPT}],
    inferenceConfig={
        # Hard ceiling on the ANSWER length, counted in tokens (roughly 3/4 of
        # a word each). This is a safety valve against a runaway bill -- if the
        # model hits the limit it simply stops mid-sentence.
        "maxTokens": 100,
        # How random the output is, from 0.0 to 1.0. Low values make the model
        # pick the most likely next word almost every time, so answers are
        # repeatable; high values make it more creative and less predictable.
        "temperature": 0.7,
    },
)

# Dig the text out of the response.
#
# That chain of keys looks tedious, but each step mirrors the request:
#   ["output"]["message"]  -- a message, with the same {role, content} shape
#                             you just sent, except role is now "assistant"
#   ["content"]            -- a list of blocks, same as your list of blocks
#   [0]["text"]            -- the first block, and its text
answer = response["output"]["message"]["content"][0]["text"]
print("AI:", answer)

# Every response also reports what it cost you. Get in the habit of looking at
# this: `inputTokens` covers your system prompt PLUS the whole message history,
# which is why a long conversation gets more expensive with every single turn.
usage = response["usage"]
print(f"\nTokens -- in: {usage['inputTokens']}, out: {usage['outputTokens']}")
