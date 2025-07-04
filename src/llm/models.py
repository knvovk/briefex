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


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class ChatCompletionMessage(BaseModel):
    role: Role
    content: str


class ChatCompletionParams(BaseModel):
    temperature: float
    max_tokens: int
    stream: bool = False


class ChatCompletionRequest(BaseModel):
    model: Model
    params: ChatCompletionParams
    messages: list[ChatCompletionMessage]


class ChatCompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    model: Model
    usage: ChatCompletionUsage
    message: ChatCompletionMessage
