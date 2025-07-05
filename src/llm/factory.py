import logging
from abc import ABC, abstractmethod
from typing import override

from .base import ChatCompletionManager
from .completion import ChatCompletionManagerImpl
from .providers import LLMProviderFactory

logger = logging.getLogger(__name__)


class ChatCompletionManagerFactory(ABC):

    @abstractmethod
    def create(self, provider_factory: LLMProviderFactory) -> ChatCompletionManager: ...


class ChatCompletionManagerFactoryImpl(ChatCompletionManagerFactory):

    @override
    def create(self, provider_factory: LLMProviderFactory) -> ChatCompletionManager:
        return ChatCompletionManagerImpl(provider_factory)


def create_chat_completion_manager_factory() -> ChatCompletionManagerFactory:
    return ChatCompletionManagerFactoryImpl()
