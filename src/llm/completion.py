from __future__ import annotations

import logging
from typing import override

from .base import ChatCompletionManager
from .exceptions import LLMCompletionError, LLMException
from .models import ChatCompletionRequest, ChatCompletionResponse, Model
from .providers import LLMProvider, LLMProviderFactory

logger = logging.getLogger(__name__)


class ChatCompletionManagerImpl(ChatCompletionManager):

    _instance: ChatCompletionManagerImpl | None = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs) -> ChatCompletionManagerImpl:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, provider_factory: LLMProviderFactory) -> None:
        if self._initialized:
            return

        super().__init__(provider_factory)
        self._provider_cache: dict[Model, LLMProvider] = {}
        self._initialized = True

    @override
    def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        logger.info(
            "Processing completion request (model=%s, temperature=%.2f, max_tokens=%d)",
            request.model,
            request.params.temperature,
            request.params.max_tokens,
        )

        provider = None
        try:
            provider = self._get_provider(request.model)
            response = provider.complete(request)

            logger.info(
                "Completion succeeded (model=%s, status=%s, "
                "prompt_tokens=%d, completion_tokens=%d, total_tokens=%d)",
                response.model,
                "None",  # TODO: response.status
                response.usage.prompt_tokens,
                response.usage.completion_tokens,
                response.usage.total_tokens,
            )
            return response

        except LLMException:
            raise

        except Exception as exc:
            logger.error("Failed to complete request: %s", exc, exc_info=True)
            raise LLMCompletionError(
                provider=provider.__class__.__name__ if provider else "None",
                reason=str(exc),
            ) from exc

    def _get_provider(self, model: Model) -> LLMProvider:
        if model not in self._provider_cache:
            provider = self._provider_factory.create(model)
            self._provider_cache[model] = provider

        return self._provider_cache[model]
