from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from briefex.llm.models import ChatCompletionRequest, ChatCompletionResponse, Model

_log = logging.getLogger(__name__)


class Provider(ABC):
    """Base class for LLM chat completion providers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._args = args
        self._kwargs = kwargs

        _log.info(
            "%s initialized with args=%r, kwargs=%r",
            self.__class__.__name__,
            args,
            kwargs,
        )

    @abstractmethod
    def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Complete the chat request and return the response.

        Args:
            request: ChatCompletionRequest containing the input prompt and parameters.

        Returns:
            ChatCompletionResponse with the provider's output.
        """


class ProviderFactory(ABC):
    """Base factory for creating Provider instances."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._provider_args = args
        self._provider_kwargs = kwargs

        _log.info(
            "%s initialized with args=%r, kwargs=%r",
            self.__class__.__name__,
            self._provider_args,
            self._provider_kwargs,
        )

    @abstractmethod
    def create(self, model: Model) -> Provider:
        """Create a Provider for the given model.

        Args:
            model: Model instance specifying the provider configuration.

        Returns:
            A Provider instance configured for the specified model.
        """
