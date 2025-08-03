from __future__ import annotations

import logging
from typing import Any, override

from briefex.crawler.models import PostDraft
from briefex.crawler.parsers.base import Parser
from briefex.crawler.parsers.registry import register

_log = logging.getLogger(__name__)


@register("generic::rss")
class GenericRSSParser(Parser):
    """Parser stub for generic RSS feeds."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        _log.info(
            "GenericRSSParser initialized as a stub for source '%s'",
            getattr(self, "_src", None) and self._src.url or "<unknown>",
        )

    @override
    def parse(self, data: bytes) -> PostDraft:
        """Parse raw RSS bytes into a single PostDraft (stub).

        Args:
            data: Raw RSS feed bytes.

        Returns:
            An empty PostDraft instance.
        """
        _log.warning(
            "GenericRSSParser.parse called for source '%s' but not implemented; "
            "returning empty PostDraft",
            getattr(self, "_src", None) and self._src.url or "<unknown>",
        )
        return PostDraft()

    @override
    def parse_many(self, data: bytes) -> list[PostDraft]:
        """Parse raw RSS bytes into multiple PostDrafts (stub).

        Args:
            data: Raw RSS feed bytes.

        Returns:
            An empty list.
        """
        _log.warning(
            "GenericRSSParser.parse_many called for source '%s' but not implemented; "
            "returning empty list",
            getattr(self, "_src", None) and self._src.url or "<unknown>",
        )
        return []
