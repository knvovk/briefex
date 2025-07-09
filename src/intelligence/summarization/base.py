import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Summarizer(ABC):

    def __init__(self, *args, **kwargs) -> None: ...

    @abstractmethod
    def summarize(self, text: str) -> str: ...
