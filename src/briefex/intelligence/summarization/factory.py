import logging
from abc import ABC, abstractmethod
from typing import override

from .base import Summarizer
from .summarizer import SummarizerImpl

logger = logging.getLogger(__name__)


class SummarizerFactory(ABC):
    """Abstract base class for summarizer factories.

    A summarizer factory is responsible for creating instances of Summarizer.
    All summarizer factories must implement the create method.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initialize a new SummarizerFactory.

        Args:
            *args: Variable length argument list to pass to the created summarizer.
            **kwargs: Arbitrary keyword arguments to pass to the created summarizer.
        """
        self._args = args
        self._kwargs = kwargs
        logger.info("%s initialized", self.__class__.__name__)

    @abstractmethod
    def create(self) -> Summarizer:
        """Create a new Summarizer instance.

        Returns:
            A new Summarizer instance.
        """
        ...


class SummarizerFactoryImpl(SummarizerFactory):
    """Implementation of SummarizerFactory.

    This class provides a concrete implementation of the SummarizerFactory
    abstract base class, creating SummarizerImpl instances.
    """

    @override
    def create(self) -> Summarizer:
        """Create a new SummarizerImpl instance.

        Returns:
            A new SummarizerImpl instance configured with the factory's arguments.
        """
        return SummarizerImpl(*self._args, **self._kwargs)


def create_summarizer_factory(*args, **kwargs) -> SummarizerFactory:
    """Create a new SummarizerFactory instance.

    This is a convenience function that creates and returns a SummarizerFactoryImpl
    instance with the provided arguments.

    Args:
        *args: Variable length argument list to pass to the factory.
        **kwargs: Arbitrary keyword arguments to pass to the factory.

    Returns:
        A new SummarizerFactory instance.
    """
    return SummarizerFactoryImpl(*args, **kwargs)
