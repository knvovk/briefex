from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from briefex.crawler.models import SourceType

_log = logging.getLogger(__name__)


class Fetcher(ABC):
    """Abstract base class for fetchers that retrieve raw data."""

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
    def fetch(self, url: str, **kwargs: Any) -> bytes:
        """Fetch raw bytes from the specified URL."""

    @abstractmethod
    def close(self) -> None:
        """Close the fetcher and release any held resources."""


class FetcherFactory(ABC):
    """Abstract base class for factories that create Fetcher instances."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._fetcher_args = args
        self._fetcher_kwargs = kwargs

        _log.info(
            "%s initialized with args=%r, kwargs=%r",
            self.__class__.__name__,
            self._fetcher_args,
            self._fetcher_kwargs,
        )

    @abstractmethod
    def create(self, src_type: SourceType) -> Fetcher:
        """Create a Fetcher for the given source type."""
