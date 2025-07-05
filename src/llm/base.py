import logging
from abc import ABC, abstractmethod

from .models import ChatCompletionRequest, ChatCompletionResponse
from .providers import LLMProviderFactory

logger = logging.getLogger(__name__)


class ChatCompletionManager(ABC):

    def __init__(self, provider_factory: LLMProviderFactory) -> None:
        self._provider_factory = provider_factory

    @abstractmethod
    def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse: ...
