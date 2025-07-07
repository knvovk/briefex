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

    @abstractmethod
    def create(self, provider_factory: LLMProviderFactory) -> ChatCompletionDispatcher:
        """Create a chat completion dispatcher.

        Args:
            provider_factory: Factory for creating LLM providers.

        Returns:
            A chat completion dispatcher instance.
        """
        ...


class ChatCompletionDispatcherFactoryImpl(ChatCompletionDispatcherFactory):
    """Implementation of the ChatCompletionDispatcherFactory interface.

    This class creates instances of ChatCompletionDispatcherFactoryImpl.
    """

    @override
    def create(self, provider_factory: LLMProviderFactory) -> ChatCompletionDispatcher:
        """Create a chat completion dispatcher.

        Args:
            provider_factory: Factory for creating LLM providers.

        Returns:
            A chat completion dispatcher instance.
        """
        return ChatCompletionDispatcherImpl(provider_factory)


def create_chat_completion_dispatcher_factory() -> ChatCompletionDispatcherFactory:
    """Create a factory for chat completion dispatchers.

    Returns:
        A factory for creating chat completion dispatchers.
    """
    return ChatCompletionDispatcherFactoryImpl()
