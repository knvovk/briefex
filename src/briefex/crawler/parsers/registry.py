from __future__ import annotations

import logging
from collections.abc import Callable

from briefex.crawler.exceptions import CrawlerConfigurationError
from briefex.crawler.models import SourceCode
from briefex.crawler.parsers.base import Parser

_log = logging.getLogger(__name__)


class ParserRegistry(dict[SourceCode, type[Parser]]):
    """Map source codes to their corresponding Parser subclasses."""

    def register(self, code: SourceCode, cls: type[Parser]) -> None:
        """Register a Parser subclass for a given source code.

        Args:
            code: SourceCode under which to register the parser.
            cls: Parser subclass to register.

        Raises:
            CrawlerConfigurationError: If cls is not a subclass of Parser.
        """
        if not isinstance(cls, type) or not issubclass(cls, Parser):
            raise CrawlerConfigurationError(
                issue=f"Class `{cls.__name__}` must be a subclass of Parser",
                stage="parser_registration",
            )

        self[code] = cls
        _log.debug("%s registered for %s", cls.__name__, code)


parser_registry = ParserRegistry()


def register(code: SourceCode) -> Callable[[type[Parser]], type[Parser]]:
    """Create a decorator to register a Parser for the given source code.

    Args:
        code: SourceCode under which to register the parser.

    Returns:
        A decorator that registers the decorated Parser subclass.
    """

    def wrapper(cls: type[Parser]) -> type[Parser]:
        """Register the decorated Parser class in the global registry.

        Args:
            cls: Parser subclass to register.

        Returns:
            The original class.

        Raises:
            CrawlerConfigurationError: If registration fails.
        """
        try:
            parser_registry.register(code, cls)
            return cls
        except CrawlerConfigurationError:
            raise
        except Exception as exc:
            _log.error("Unexpected error during parser registration: %s", exc)
            raise CrawlerConfigurationError(
                issue=f"`{cls.__name__}` registration failed",
                stage="parser_registration",
            ) from exc

    return wrapper
