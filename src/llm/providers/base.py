import logging
from abc import ABC, abstractmethod

from ..models import ChatCompletionRequest, ChatCompletionResponse

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    This class defines the interface for language model providers that can
    process chat completion requests and return responses.
    """

    def __init__(self, **kwargs) -> None:
        """Initialize the LLM provider.

        Args:
            **kwargs: Provider-specific configuration parameters.
        """
        ...

    @abstractmethod
    def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Process a chat completion request and return a response.

        Args:
            request: The chat completion request containing messages and model information.

        Returns:
            A chat completion response from the language model.

        Raises:
            LLMException: If an error occurs during completion.
        """
        ...
