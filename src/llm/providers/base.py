import logging
from abc import ABC, abstractmethod

from ..models import ChatCompletionRequest, ChatCompletionResponse

logger = logging.getLogger(__name__)


class LLMProvider(ABC):

    def __init__(self, **kwargs) -> None: ...

    @abstractmethod
    def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse: ...
