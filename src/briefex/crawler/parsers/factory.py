from __future__ import annotations

import logging
from typing import override

from briefex.crawler.exceptions import CrawlerConfigurationError
from briefex.crawler.models import Source
from briefex.crawler.parsers.base import Parser, ParserFactory
from briefex.crawler.parsers.registry import parser_registry

_log = logging.getLogger(__name__)


class DefaultParserFactory(ParserFactory):
    """Factory that selects and instantiates a Parser based on Source code."""

    @override
    def create(self, src: Source) -> Parser:
        """Instantiate a Parser for the given Source.

        Args:
            src: Source instance specifying parser code.

        Returns:
            A Parser instance appropriate for the source.

        Raises:
            CrawlerConfigurationError: If no parser is registered for src.code
                or if instantiation fails.
        """
        _log.debug("Initializing parser for %s", src)
        if src.code_name not in parser_registry:
            raise CrawlerConfigurationError(
                issue=f"No parser registered for {src.code_name}",
                stage="parser_selection",
            )

        parser_cls = parser_registry[src.code_name]
        try:
            instance = parser_cls(src)
            _log.info("%s initialized for %s", parser_cls.__name__, src)
            return instance

        except Exception as exc:
            _log.error("Unexpected error during parser instantiation: %s", exc)
            raise CrawlerConfigurationError(
                issue=f"Parser instantiation failed for {parser_cls.__name__}: {exc}",
                stage="parser_instantiation",
            ) from exc
