import logging
from abc import ABC, abstractmethod
from typing import override

from .base import ChatCompletionManager
from .completion import ChatCompletionManagerImpl
from .providers import LLMProviderFactory

logger = logging.getLogger(__name__)


class ChatCompletionManagerFactory(ABC):
    """Abstract factory for creating chat completion managers.

    This class defines the interface for factories that create chat completion managers.
    """

    @abstractmethod
    def create(self, provider_factory: LLMProviderFactory) -> ChatCompletionManager:
        """Create a chat completion manager.

        Args:
            provider_factory: Factory for creating LLM providers.

        Returns:
            A chat completion manager instance.
        """
        ...


class ChatCompletionManagerFactoryImpl(ChatCompletionManagerFactory):
    """Implementation of the ChatCompletionManagerFactory interface.

    This class creates instances of ChatCompletionManagerImpl.
    """

    @override
    def create(self, provider_factory: LLMProviderFactory) -> ChatCompletionManager:
        """Create a chat completion manager.

        Args:
            provider_factory: Factory for creating LLM providers.

        Returns:
            A chat completion manager instance.
        """
        return ChatCompletionManagerImpl(provider_factory)


def create_chat_completion_manager_factory() -> ChatCompletionManagerFactory:
    """Create a factory for chat completion managers.

    Returns:
        A factory for creating chat completion managers.
    """
    return ChatCompletionManagerFactoryImpl()
