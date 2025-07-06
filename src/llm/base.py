import logging
from abc import ABC, abstractmethod

from .models import ChatCompletionRequest, ChatCompletionResponse
from .providers import LLMProviderFactory

logger = logging.getLogger(__name__)


class ChatCompletionManager(ABC):
    """Abstract base class for chat completion managers.

    This class defines the interface for chat completion managers that handle
    requests to language models and return their responses.

    Attributes:
        _provider_factory: Factory for creating LLM providers.
    """

    def __init__(self, provider_factory: LLMProviderFactory) -> None:
        """Initialize the chat completion manager.

        Args:
            provider_factory: Factory for creating LLM providers.
        """
        self._provider_factory = provider_factory

    @abstractmethod
    def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Process a chat completion request and return a response.

        Args:
            request: The chat completion request containing messages and model information.

        Returns:
            A chat completion response from the language model.
        """
        ...
