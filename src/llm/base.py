import logging
from abc import ABC, abstractmethod

from .models import ChatCompletionRequest, ChatCompletionResponse

logger = logging.getLogger(__name__)


class LLMClient(ABC):

    def __init__(self, *args, **kwargs) -> None: ...

    @abstractmethod
    def completions(self, req: ChatCompletionRequest) -> ChatCompletionResponse: ...
