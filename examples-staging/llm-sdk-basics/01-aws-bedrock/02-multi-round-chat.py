# -*- coding: utf-8 -*-

"""
Step 2 of 3 -- Hold a 3-turn conversation by managing the history by hand.

Here is the single most surprising fact about every LLM API on the market:

    The model has NO memory. Each API call is completely independent.

There is no session on the server, nothing is stored between calls, and the
model cannot recall what it told you a second ago. What creates the illusion of
memory is that YOU resend the entire conversation every single time. Turn 3
works only because the request carries turns 1 and 2 inside it.

So the loop you must run yourself is:

    1. append your new question to the history      (role="user")
    2. send the WHOLE history
    3. append the model's reply back into it        (role="assistant")

Miss step 3 and the model develops amnesia -- it will never see its own
previous answers, so it cannot follow up on them.

The conversation below is built to prove the memory is real: the last question
can only be answered from turn 1, which by then is ancient history.

Cost warning: because every turn resends everything before it, input tokens grow
quadratically over a long chat. Watch the token counts printed at the end.

Requires: nothing extra -- boto3 is already a core dependency of this project.

Credentials: AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, or any other
credential source boto3 already knows about (e.g. `~/.aws/credentials`).

Run it:
    .venv/bin/python examples-staging/llm-sdk-basics/01-aws-bedrock/02-multi-round-chat.py
"""

import os

import boto3
from dotenv import load_dotenv

# See 01-single-message.py for why we do not put AWS keys in .env.
load_dotenv()

session = boto3.Session(region_name=os.environ.get("AWS_REGION", "us-east-1"))
bedrock = session.client("bedrock-runtime")

MODEL_ID = "us.amazon.nova-micro-v1:0"
SYSTEM_PROMPT = "You are a helpful assistant. Answer in one short sentence."

# The three things we will say, in order. Read them as a test: the third one is
# unanswerable unless the model can still see the first.
QUESTIONS = [
    "My favorite number is 7. Just acknowledge it.",
    "Double my favorite number.",
    "What was my favorite number before you doubled it?",
]

# THE conversation history. This list is the entire "memory" of the chat -- it
# lives here in your Python process, not on Amazon's servers. It starts empty
# and grows by two entries per turn (your message, then the model's reply).
messages = []

for i, question in enumerate(QUESTIONS, start=1):
    print(f"\n===== Turn {i} =====")
    print("You:", question)

    # --- Step 1: append what you are about to say -------------------------
    # Note we APPEND rather than replace. Everything said earlier stays.
    messages.append(
        {
            "role": "user",
            "content": [{"text": question}],
        }
    )

    # --- Step 2: send the whole history ----------------------------------
    # `messages` is the full transcript, not just the new question. On turn 3
    # this list already holds 5 entries and all 5 get uploaded again.
    response = bedrock.converse(
        modelId=MODEL_ID,
        messages=messages,
        system=[{"text": SYSTEM_PROMPT}],
        inferenceConfig={"maxTokens": 100, "temperature": 0.7},
    )

    # --- Step 3: append the reply back into the history -------------------
    # This is the step beginners forget. Conveniently, the object at
    # response["output"]["message"] already has the exact {role, content}
    # shape the history wants (with role="assistant"), so it drops straight
    # in with no conversion.
    reply = response["output"]["message"]
    messages.append(reply)

    print("AI:", reply["content"][0]["text"])

    # Watch `inputTokens` climb on every turn even though your questions stay
    # the same length. That growth IS the resent history -- it is the price of
    # memory, and it is why production apps eventually trim or summarize old
    # turns instead of keeping everything forever.
    usage = response["usage"]
    print(f"Tokens -- in: {usage['inputTokens']}, out: {usage['outputTokens']}")

# The finished transcript: 3 questions + 3 answers = 6 entries. Notice that it
# is nothing but a plain Python list of plain dicts. There is no magic here,
# which is exactly what makes step 3 easy to wrap in a class -- see
# 03-chat-session-class.py.
print(f"\n===== Done: history holds {len(messages)} messages =====")
