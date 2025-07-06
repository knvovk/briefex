from enum import Enum
from typing import Literal

from pydantic import BaseModel

Model = Literal[
    "yandexgpt",
    "yandexgpt-lite",
    "GigaChat-2",
    "GigaChat-2-Pro",
    "GigaChat-2-Max",
]
"""Type alias for supported LLM models.

This type defines the supported language models that can be used for chat completions.
"""


class Role(str, Enum):
    """Enumeration of possible roles in a chat conversation.

    These roles define who is speaking in a chat message.

    Attributes:
        SYSTEM: System message providing context or instructions.
        USER: Message from the user.
        ASSISTANT: Message from the assistant (AI).
        FUNCTION: Message from a function call.
    """

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class ChatCompletionMessage(BaseModel):
    """Model representing a message in a chat conversation.

    Attributes:
        role: The role of the entity sending the message.
        content: The content of the message.
    """

    role: Role
    content: str


class ChatCompletionParams(BaseModel):
    """Parameters for controlling the chat completion generation.

    Attributes:
        temperature: Controls randomness in the output. Higher values (e.g., 0.8)
            make the output more random, lower values (e.g., 0.2)
            make it more deterministic.
        max_tokens: The maximum number of tokens to generate in the completion.
        stream: Whether to stream the response or not. Defaults to False.
    """

    temperature: float
    max_tokens: int
    stream: bool = False


class ChatCompletionRequest(BaseModel):
    """Request model for chat completion.

    Attributes:
        model: The language model to use for completion.
        params: Parameters controlling the completion generation.
        messages: List of messages in the conversation history.
    """

    model: Model
    params: ChatCompletionParams
    messages: list[ChatCompletionMessage]


class ChatCompletionUsage(BaseModel):
    """Token usage information for a chat completion.

    Attributes:
        prompt_tokens: Number of tokens in the prompt.
        completion_tokens: Number of tokens in the completion.
        total_tokens: Total number of tokens used (prompt + completion).
    """

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """Response model for chat completion.

    Attributes:
        model: The language model used for completion.
        usage: Token usage information.
        message: The generated message from the assistant.
    """

    model: Model
    usage: ChatCompletionUsage
    message: ChatCompletionMessage
