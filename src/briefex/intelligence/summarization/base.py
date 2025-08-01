from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

_log = logging.getLogger(__name__)


class Summarizer(ABC):
    """Interface for text summarization implementations."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._args = args
        self._kwargs = kwargs

        _log.info(
            "%s initialized with args=%r, kwargs=%r",
            self.__class__.__name__,
            args,
            kwargs,
        )

    @abstractmethod
    def summarize(self, text: str) -> str:
        """Generate a concise summary for the input text.

        Args:
            text: The text to summarize.

        Returns:
            A summarized version of the input text.
        """


class SummarizerFactory(ABC):
    """Interface for factories that create Summarizer instances."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._summarizer_args = args
        self._summarizer_kwargs = kwargs

        _log.info(
            "%s initialized with args=%r, kwargs=%r",
            self.__class__.__name__,
            self._summarizer_args,
            self._summarizer_kwargs,
        )

    @abstractmethod
    def create(self) -> Summarizer:
        """Instantiate and return a Summarizer."""
