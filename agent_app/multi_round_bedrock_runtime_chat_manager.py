# -*- coding: utf-8 -*-

"""
Multi-round chat session manager for AWS Bedrock Runtime.

This module provides a high-level wrapper around the boto3 Bedrock Runtime
Converse API, making it easier to manage multi-turn conversations with AI models.

Key features:
- Manages conversation history automatically
- Provides convenient methods for sending text messages

Everything the Converse API sends and returns is a plain dict, and this module
keeps it that way. It deliberately depends on no typed-wrapper or type-stub
package: those add a third-party dependency on top of boto3 just for editor
autocompletion, and when one lags behind a boto3 release it breaks the install
for everyone. The type aliases below name the dict shapes so the signatures stay
readable without that cost.

Dependencies:
- func_args: Utility for handling optional parameters in function calls.
"""

import typing as T
import sys
import dataclasses

from func_args.api import (
    OPT,
    remove_optional,
)  # OPT marks optional fields, remove_optional strips them

from rich import print as rprint  # Pretty printing for debugging

from .utils import debug

#: Shapes exchanged with the Bedrock Converse API. They are all plain dicts;
#: these aliases exist purely to make the signatures below self-documenting.
#: See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-runtime/client/converse.html
SystemContentBlock = dict[str, T.Any]  # e.g. {"text": "You are a helpful assistant."}
Message = dict[str, T.Any]  # e.g. {"role": "user", "content": [{"text": "Hi"}]}
ConverseResponse = dict[str, T.Any]  # the raw converse() return value


@dataclasses.dataclass
class ChatSession:
    """
    Manages a multi-turn chat session with AWS Bedrock.

    This class wraps the Bedrock Converse API to provide:
    - Automatic conversation history management
    - Simple interface for sending messages

    Attributes:
        client: The boto3 Bedrock Runtime client instance.
        model_id: The Bedrock model ID (e.g., "us.amazon.nova-micro-v1:0").
        system: Optional system prompt blocks that define AI behavior.

    Example:
        >>> session = ChatSession(
        ...     client=bedrock_runtime_client,
        ...     model_id="us.amazon.nova-micro-v1:0",
        ...     system=[{"text": "You are a helpful assistant."}],
        ... )
        >>> response = session.send_text_message("Hello!")
        >>> print(response["output"]["message"]["content"][0]["text"])
    """

    # Required: boto3 Bedrock Runtime client. Annotated loosely because boto3
    # builds its service clients at runtime, so there is no importable class.
    client: T.Any = dataclasses.field()
    # Required: Model ID to use for inference
    model_id: str = dataclasses.field()
    # Optional: System prompt defining AI behavior and context
    system: T.Sequence[SystemContentBlock] = dataclasses.field(default=OPT)

    # Internal: Unique session identifier (can be overwritten for session continuity)
    _session_id: str = dataclasses.field(init=False)
    # Internal: Accumulated conversation history (user + assistant messages)
    _messages: list[Message] = dataclasses.field(init=False)

    def __post_init__(self):
        """Initialize internal state after dataclass construction."""
        self._session_id = "abc"  # Default session ID, typically overwritten
        self._messages = []  # Start with empty conversation history

    def send_message(
        self,
        messages: T.Sequence[Message],
    ) -> ConverseResponse:
        """
        Send message(s) to the AI and get a response.

        This method:
        1. Appends new messages to conversation history
        2. Calls the Bedrock Converse API with full history
        3. Appends the AI's response to history for future turns
        4. Returns the raw response dict

        Args:
            messages: List of message blocks to send. Each message should have
                      'role' ('user' or 'assistant') and 'content' fields.

        Returns:
            ConverseResponse: Raw response dict with output text, usage stats, etc.
                Access the response text via:
                ``response["output"]["message"]["content"][0]["text"]``
        """
        print("===== Send message")

        # Append new messages to conversation history
        self._messages.extend(messages)

        # Build API request parameters
        kwargs = dict(
            modelId=self.model_id,
            messages=self._messages,  # Full conversation history
            system=self.system,  # System prompt (if any)
        )
        kwargs = remove_optional(**kwargs)  # Strip None/OPT values

        # Debug: Print outgoing request
        print("----- Converse kwargs:")
        rprint(kwargs)

        # Call Bedrock Converse API. The return value is a plain dict.
        response = self.client.converse(**kwargs)

        # Debug: Print response (excluding metadata noise)
        print("----- Converse response:")
        response.pop("ResponseMetadata", None)
        rprint(response)

        # Append AI's response to history for multi-turn context
        self._messages.append(response["output"]["message"])

        return response

    def send_text_message(
        self,
        message: str,
    ) -> ConverseResponse:
        """
        Convenience method to send a simple text message.

        Wraps the message string in the required Bedrock message format
        and calls send_message().

        Args:
            message: Plain text message from the user.

        Returns:
            ConverseResponse: The AI's response.
        """
        return self.send_message(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": message,
                        },
                    ],
                }
            ],
        )

    def debug_response(self, response: ConverseResponse) -> str:
        """
        Log response for debugging.
        """
        debug("------ Chat response")
        output_text = response["output"]["message"]["content"][0]["text"]
        debug(output_text)
        debug("------ Token Usage")
        debug(str(response["usage"]))
        sys.stderr.flush()
        return output_text
