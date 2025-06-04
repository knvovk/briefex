import logging
from abc import ABC, abstractmethod

from ..models import SourceType

logger = logging.getLogger(__name__)


class BaseFetcher(ABC):

    def __init__(self, *args, **kwargs) -> None: ...

    @abstractmethod
    def fetch(self, url: str) -> bytes: ...


class BaseFetcherFactory(ABC):

    @abstractmethod
    def create(self, src_type: SourceType, *args, **kwargs) -> BaseFetcher: ...
