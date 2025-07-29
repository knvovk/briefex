from __future__ import annotations

from typing import Any

import briefex.llm.sber  # noqa: F401
import briefex.llm.yandex  # noqa: F401
from briefex.llm.base import Provider, ProviderFactory
from briefex.llm.exceptions import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMException,
    LLMRequestError,
    LLMResponseError,
)
from briefex.llm.factory import DefaultProviderFactory
from briefex.llm.models import (
    ChatCompletionMessage,
    ChatCompletionParams,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionStatus,
    ChatCompletionUsage,
    Model,
    Role,
)

_provider_factory: ProviderFactory | None = None


def get_default_provider_factory(*args: Any, **kwargs: Any) -> ProviderFactory:
    global _provider_factory

    if _provider_factory is None:
        _provider_factory = DefaultProviderFactory(*args, **kwargs)

    return _provider_factory


__all__ = [
    "Provider",
    "ProviderFactory",
    "LLMAuthenticationError",
    "LLMConfigurationError",
    "LLMException",
    "LLMRequestError",
    "LLMResponseError",
    "ChatCompletionMessage",
    "ChatCompletionParams",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "ChatCompletionStatus",
    "ChatCompletionUsage",
    "Model",
    "Role",
    "get_default_provider_factory",
]
