import logging
from abc import ABC, abstractmethod

from ..models import PostDraft, Source

logger = logging.getLogger(__name__)


class Parser(ABC):

    def __init__(self, src: Source) -> None:
        self._src = src

    @abstractmethod
    def parse_one(self, data: bytes) -> PostDraft: ...

    @abstractmethod
    def parse_many(self, data: bytes) -> list[PostDraft]: ...
