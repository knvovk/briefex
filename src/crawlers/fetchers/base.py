import logging
from abc import ABC, abstractmethod

from ..models import SourceType

logger = logging.getLogger(__name__)


class BaseFetcher(ABC):

    def __init__(self, *args, **kwargs) -> None: ...

    @abstractmethod
    def fetch(self, url: str) -> bytes: ...

    @abstractmethod
    def close(self) -> None: ...


class BaseFetcherFactory(ABC):

    def __init__(self, *args, **kwargs) -> None:
        self._args = args
        self._kwargs = kwargs

    @abstractmethod
    def create(self, src_type: SourceType) -> BaseFetcher: ...
