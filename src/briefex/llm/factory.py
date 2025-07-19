import logging
from abc import ABC, abstractmethod
from typing import override

from .base import ChatCompletionDispatcher
from .completion import ChatCompletionDispatcherImpl
from .providers import LLMProviderFactory

logger = logging.getLogger(__name__)


class ChatCompletionDispatcherFactory(ABC):
    """Abstract factory for creating chat completion dispatchers.

    This class defines the interface for factories
    that create chat completion dispatchers.
    """

    def __init__(self, provider_factory: LLMProviderFactory) -> None:
        """Initialize a new ChatCompletionDispatcherFactory.

        Args:
            provider_factory: Factory for creating LLM providers.
        """
        self._provider_factory = provider_factory
        logger.info("%s initialized", self.__class__.__name__)

    @abstractmethod
    def create(self) -> ChatCompletionDispatcher:
        """Create a chat completion dispatcher.

        Returns:
            A chat completion dispatcher instance.
        """
        ...


class ChatCompletionDispatcherFactoryImpl(ChatCompletionDispatcherFactory):
    """Implementation of the ChatCompletionDispatcherFactory interface.

    This class creates instances of ChatCompletionDispatcherFactoryImpl.
    """

    @override
    def create(self) -> ChatCompletionDispatcher:
        """Create a chat completion dispatcher.

        Args:
            provider_factory: Factory for creating LLM providers.

        Returns:
            A chat completion dispatcher instance.
        """
        return ChatCompletionDispatcherImpl(self._provider_factory)


def create_chat_completion_dispatcher_factory(
    provider_factory: LLMProviderFactory,
) -> ChatCompletionDispatcherFactory:
    """Create a factory for chat completion dispatchers.

    Returns:
        A factory for creating chat completion dispatchers.
    """
    return ChatCompletionDispatcherFactoryImpl(provider_factory)
