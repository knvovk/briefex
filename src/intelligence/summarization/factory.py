import logging
from abc import ABC, abstractmethod
from typing import override

from .base import Summarizer
from .summarizer import SummarizerImpl

logger = logging.getLogger(__name__)


class SummarizerFactory(ABC):

    def __init__(self, *args, **kwargs) -> None:
        self._args = args
        self._kwargs = kwargs
        logger.info("%s initialized", self.__class__.__name__)

    @abstractmethod
    def create(self) -> Summarizer: ...


class SummarizerFactoryImpl(SummarizerFactory):

    @override
    def create(self) -> Summarizer:
        return SummarizerImpl(*self._args, **self._kwargs)


def create_summarizer_factory(*args, **kwargs) -> SummarizerFactory:
    return SummarizerFactoryImpl(*args, **kwargs)
