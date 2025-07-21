from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from ..models import PostDraft, Source

_log = logging.getLogger(__name__)


class Parser(ABC):
    """Abstract base class for parsing single or multiple posts from source data."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _log.info(
            "%s initialized with args=%r, kwargs=%r",
            self.__class__.__name__,
            args,
            kwargs,
        )

    @abstractmethod
    def parse(self, src: Source, data: bytes) -> PostDraft:
        """Parse raw bytes into a single PostDraft.

        Args:
            src: Source configuration for parsing.
            data: Raw content bytes to parse.

        Returns:
            A PostDraft instance extracted from the data.
        """

    @abstractmethod
    def parse_many(self, src: Source, data: bytes) -> list[PostDraft]:
        """Parse raw bytes into multiple PostDrafts.

        Args:
            src: Source configuration for parsing.
            data: Raw content bytes to parse.

        Returns:
            A list of PostDraft instances extracted from the data.
        """


class ParserFactory(ABC):
    """Abstract base class for factories that create Parser instances."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _log.info(
            "%s initialized with args=%r, kwargs=%r",
            self.__class__.__name__,
            args,
            kwargs,
        )

    @abstractmethod
    def create(self, src: Source) -> Parser:
        """Create a Parser for the given source.

        Args:
            src: Source configuration to select the parser.

        Returns:
            A Parser instance appropriate for the source.
        """
