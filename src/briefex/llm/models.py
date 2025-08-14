from __future__ import annotations

import logging
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel

_log = logging.getLogger(__name__)


Model = Literal[
    "yandexgpt",
    "yandexgpt-lite",
    "GigaChat-2",
    "GigaChat-2-Pro",
    "GigaChat-2-Max",
    "STUB",
    "Stub",
    "stub",
]
"""Supported model identifiers for chat completion."""


class ChatCompletionStatus(StrEnum):
    """Enumeration of possible statuses for a chat completion response."""

    ERROR = "error"
    CONTENT_FILTERED = "content_filtered"
    TRUNCATED = "truncated"
    FUNCTION_CALL = "function_call"
    FINISHED = "finished"
    UNDEFINED = "undefined"


class Role(StrEnum):
    """Roles that a chat message can have."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class ChatCompletionMessage(BaseModel):
    """Represents a single chat message with role and content."""

    role: Role
    content: str


class ChatCompletionParams(BaseModel):
    """Generation parameters for a chat completion request."""

    temperature: float
    max_tokens: int
    stream: bool = False


class ChatCompletionRequest(BaseModel):
    """Payload for requesting a chat completion."""

    model: Model
    params: ChatCompletionParams
    messages: list[ChatCompletionMessage]


class ChatCompletionUsage(BaseModel):
    """Token usage statistics returned in a completion response."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """Response from a chat completion request."""

    model: Model
    usage: ChatCompletionUsage
    status: ChatCompletionStatus
    message: ChatCompletionMessage
