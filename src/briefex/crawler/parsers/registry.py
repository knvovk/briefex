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
            message = f"Cannot register '{cls.__name__}': not a Parser subclass"
            _log.error(message)
            raise CrawlerConfigurationError(
                issue=message,
                stage="parser_registration",
            )

        self[code] = cls
        _log.info(
            "Parser '%s' successfully registered for source code '%s'",
            cls.__name__,
            code,
        )


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
        _log.debug(
            "Attempting to register parser '%s' for source code '%s'",
            cls.__name__,
            code,
        )
        try:
            parser_registry.register(code, cls)
            _log.debug(
                "Registered parser '%s' for source code '%s'",
                cls.__name__,
                code,
            )
            return cls

        except CrawlerConfigurationError:
            raise

        except Exception as exc:
            _log.error(
                "Unexpected error registering parser '%s' for source code '%s': %s",
                cls.__name__,
                code,
                exc,
            )
            raise CrawlerConfigurationError(
                issue=f"Registration failed for '{cls.__name__}'",
                stage="parser_registration",
            ) from exc

    return wrapper
