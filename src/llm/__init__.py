"""LLM (Language Model) package for interacting with various LLM providers.

This package provides a unified interface for interacting with different language model
providers such as Yandex GPT and GigaChat. It includes classes for managing chat completions,
handling requests and responses, and dealing with various error conditions.

The package is organized into several modules:
- base: Contains abstract base classes defining the interfaces
- completion: Contains implementations of the chat completion manager
- exceptions: Contains exception classes for error handling
- factory: Contains factory classes for creating managers
- models: Contains data models for requests and responses
- providers: Contains provider-specific implementations
"""

from .base import ChatCompletionManager
from .factory import (
    ChatCompletionManagerFactory,
    create_chat_completion_manager_factory,
)
from .models import (
    ChatCompletionMessage,
    ChatCompletionParams,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionUsage,
    Role,
)
from .providers import *

__all__ = [
    "ChatCompletionManager",
    "ChatCompletionManagerFactory",
    "create_chat_completion_manager_factory",
    "ChatCompletionMessage",
    "ChatCompletionParams",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "ChatCompletionUsage",
    "Role",
    "LLMProvider",
    "LLMProviderFactory",
    "create_llm_provider_factory",
]
