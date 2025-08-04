from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

from briefex.crawler.exceptions import CrawlerConfigurationError
from briefex.crawler.parsers.base import Parser, ParserFactory
from briefex.crawler.parsers.registry import parser_registry

if TYPE_CHECKING:
    from briefex.crawler.models import Source

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
        _log.debug("Selecting parser for source code '%s'", src.code_name)
        if src.code_name not in parser_registry:
            message = f"No parser registered for source code '{src.code_name}'"
            _log.error(message)
            raise CrawlerConfigurationError(
                issue=message,
                stage="parser_selection",
            )

        parser_cls = parser_registry[src.code_name]
        try:
            instance = parser_cls(src)
            _log.info(
                "Parser '%s' instantiated successfully for source code '%s'",
                parser_cls.__name__,
                src.code_name,
            )
            return instance

        except Exception as exc:
            _log.error(
                "Failed to instantiate parser '%s' for source code '%s': %s",
                parser_cls.__name__,
                src.code_name,
                exc,
            )
            raise CrawlerConfigurationError(
                issue=f"Instantiation error in '{parser_cls.__name__}': {exc}",
                stage="parser_instantiation",
            ) from exc
