import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseFetcher(ABC):

    def __init__(self, *args, **kwargs) -> None: ...

    @abstractmethod
    def fetch(self, url: str) -> bytes: ...

    @abstractmethod
    def close(self) -> None: ...
