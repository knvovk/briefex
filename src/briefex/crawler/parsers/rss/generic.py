from __future__ import annotations

import logging
from typing import Any, override

from briefex.crawler.models import PostDraft, Source
from briefex.crawler.parsers.base import Parser
from briefex.crawler.parsers.registry import register

_log = logging.getLogger(__name__)


@register("rss::generic")
class GenericRSSParser(Parser):
    """Parser stub for generic RSS feeds."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        _log.debug("%s initialized (not implemented)", self.__class__.__name__)

    @override
    def parse(self, src: Source, data: bytes) -> PostDraft:
        """Parse raw RSS bytes into a single PostDraft (stub).

        Args:
            src: Source configuration for parsing.
            data: Raw RSS feed bytes.

        Returns:
            An empty PostDraft instance.
        """
        _log.warning("%s not implemented", self.__class__.__name__)
        return PostDraft()

    @override
    def parse_many(self, src: Source, data: bytes) -> list[PostDraft]:
        """Parse raw RSS bytes into multiple PostDrafts (stub).

        Args:
            src: Source configuration for parsing.
            data: Raw RSS feed bytes.

        Returns:
            An empty list.
        """
        _log.warning("%s not implemented", self.__class__.__name__)
        return []
