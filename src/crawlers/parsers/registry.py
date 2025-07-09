import logging
from typing import Callable

from ..exceptions import CrawlerConfigurationError
from .base import Parser

logger = logging.getLogger(__name__)


class ParserRegistry(dict[str, type[Parser]]):
    """Registry for parser classes.

    This class extends dict to provide a registry for parser classes,
    mapping source code names to parser classes.
    """

    def register(self, code_name: str, cls: type[Parser]) -> None:
        """Register a parser class for a source code name.

        Args:
            code_name: The code name of the source to register the parser for.
            cls: The parser class to register.

        Raises:
            CrawlerConfigurationError: If the class is not a valid parser class.
        """
        self._validate_parser_class(cls)
        self[code_name] = cls
        logger.debug("%s registered for %s", cls.__name__, code_name)

    def _validate_parser_class(self, cls: type[Parser]) -> None:
        """Validate that a class is a valid parser class.

        Args:
            cls: The class to validate.

        Raises:
            CrawlerConfigurationError: If the class is not a valid parser class.
        """
        if not isinstance(cls, type) or not issubclass(cls, Parser):
            raise CrawlerConfigurationError(
                issue=f"Class {cls.__name__} must be a subclass of Parser",
                component="parser_registration",
            )

    def get_parser_names(self) -> list[str]:
        """Get the names of all registered parser classes.

        Returns:
            A list of parser class names.
        """
        return [cls.__name__ for cls in self.values()]


parser_registry = ParserRegistry()
"""Global registry for parser classes."""


def register(code_name: str) -> Callable[[type[Parser]], type[Parser]]:
    """Decorator to register a parser class for a source code name.

    This decorator registers a parser class with the global parser registry.

    Args:
        code_name: The code name of the source to register the parser for.

    Returns:
        A decorator function that registers the decorated class.

    Example:
        @register("example_source")
        class ExampleParser(Parser):
            ...
    """

    def decorator(cls: type[Parser]) -> type[Parser]:
        """Register a parser class and return it.

        Args:
            cls: The parser class to register.

        Returns:
            The registered parser class.

        Raises:
            CrawlerConfigurationError: If registration fails.
        """
        try:
            parser_registry.register(code_name, cls)
            return cls
        except CrawlerConfigurationError:
            raise
        except Exception as exc:
            logger.error("Unexpected error during parser registration: %s", exc)
            raise CrawlerConfigurationError(
                issue=f"Registration failed for {cls.__name__}: {exc}",
                component="parser_registration",
            ) from exc

    return decorator
