from __future__ import annotations

import logging
from typing import override

from .base import ChatCompletionDispatcher
from .exceptions import LLMCompletionError, LLMException
from .models import ChatCompletionRequest, ChatCompletionResponse, Model
from .providers import LLMProvider, LLMProviderFactory

logger = logging.getLogger(__name__)


class ChatCompletionDispatcherImpl(ChatCompletionDispatcher):
    """Implementation of the ChatCompletionDispatcher interface.

    This class implements the singleton pattern and manages
    LLM providers for different models.
    It caches providers to avoid recreating them for later requests.

    Attributes:
        _instance: Singleton instance of this class.
        _initialized: Flag indicating if the instance has been initialized.
        _provider_cache: Cache of LLM providers indexed by a model.
    """

    _instance: ChatCompletionDispatcherImpl | None = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs) -> ChatCompletionDispatcherImpl:
        """Create or return the singleton instance of ChatCompletionDispatcherImpl.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The singleton instance of ChatCompletionDispatcherImpl.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, provider_factory: LLMProviderFactory) -> None:
        """Initialize the chat completion dispatcher.

        This method is only executed once due to the singleton pattern.

        Args:
            provider_factory: Factory for creating LLM providers.
        """
        if self._initialized:
            return

        super().__init__(provider_factory)
        self._provider_cache: dict[Model, LLMProvider] = {}
        self._initialized = True

    @override
    def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Process a chat completion request and return a response.

        This method logs the request details, gets the appropriate provider for the
        requested model, and handles any exceptions that occur during processing.

        Args:
            request: The chat completion request containing messages and model info.

        Returns:
            A chat completion response from the language model.

        Raises:
            LLMException: If an LLM-specific exception occurs.
            LLMCompletionError: If any other exception occurs during completion.
        """
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
        """Get or create a provider for the specified model.

        This method caches providers to avoid recreating them for later requests.

        Args:
            model: The model to get a provider for.

        Returns:
            An LLM provider for the specified model.
        """
        if model not in self._provider_cache:
            provider = self._provider_factory.create(model)
            self._provider_cache[model] = provider

        return self._provider_cache[model]
