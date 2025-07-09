import logging
from abc import ABC, abstractmethod
from typing import override

from ..exceptions import CrawlerConfigurationError
from ..models import Source
from .base import Parser
from .registry import parser_registry

logger = logging.getLogger(__name__)


class ParserFactory(ABC):
    """Abstract base class for parser factories.

    A parser factory is responsible for creating parser instances.
    Different implementations can create different types of parsers.

    All parser factories must implement the create method.
    """

    @abstractmethod
    def create(self, src: Source) -> Parser:
        """Create a new parser for a source.

        Args:
            src: The source to create a parser for.

        Returns:
            A new parser instance configured for the source.
        """
        ...


class ParserFactoryImpl(ParserFactory):
    """Implementation of the ParserFactory abstract class.

    This class provides a concrete implementation of the ParserFactory interface,
    creating parsers based on the source's code_name.
    """

    def __init__(self) -> None:
        """Initialize a new ParserFactoryImpl.

        Logs information about the registered parsers during initialization.
        """
        super().__init__()
        self._log_initialization()

    @override
    def create(self, src: Source) -> Parser:
        """Create a new parser for a source.

        This method gets the appropriate parser class for the source's code_name
        and instantiates it with the source.

        Args:
            src: The source to create a parser for.

        Returns:
            A new parser instance configured for the source.

        Raises:
            CrawlerConfigurationError: If no parser is registered for the source's code_name
                or if the parser instantiation fails.
        """
        logger.debug("Initializing parser for %s", src)
        cls = self._get_parser_class(src.code_name)
        return self._instantiate_parser(cls, src)

    def _get_parser_class(self, code_name: str) -> type[Parser] | None:
        """Get the parser class for a source code_name.

        Args:
            code_name: The code_name of the source to get a parser class for.

        Returns:
            The parser class for the source code_name.

        Raises:
            CrawlerConfigurationError: If no parser is registered for the source code_name.
        """
        if code_name not in parser_registry:
            available_parsers = parser_registry.get_parser_names()
            parsers_str = ", ".join(available_parsers) if available_parsers else "None"
            raise CrawlerConfigurationError(
                issue=f"No parser registered for source with code_name {code_name}. "
                f"Available parsers: {parsers_str}",
                component="parser_selection",
            )

        return parser_registry[code_name]

    def _instantiate_parser(self, cls: type[Parser], src: Source) -> Parser:
        """Instantiate a parser from a class.

        Args:
            cls: The parser class to instantiate.
            src: The source to configure the parser for.

        Returns:
            A new parser instance.

        Raises:
            CrawlerConfigurationError: If the parser instantiation fails.
        """
        try:
            parser = cls(src)
            logger.info("%s initialized for %s", cls.__name__, src)
            return parser
        except Exception as exc:
            logger.error("Unexpected error during parser instantiation: %s", exc)
            raise CrawlerConfigurationError(
                issue=f"Parser instantiation failed for {cls.__name__}: {exc}",
                component="parser_instantiation",
            ) from exc

    def _log_initialization(self) -> None:
        """Log information about the initialized factory.

        This method logs the number and names of registered parsers.
        """
        parser_count = len(parser_registry)
        if parser_count == 0:
            logger.warning("ParserFactory initialized with no registered parsers")
            return

        parser_names = parser_registry.get_parser_names()
        logger.info(
            "ParserFactory initialized with %d parser%s: %s",
            parser_count,
            "s" if parser_count > 1 else "",
            ", ".join(parser_names),
        )


def create_parser_factory() -> ParserFactory:
    """Create a new parser factory.

    This function is the main entry point for creating parser factories.
    It creates and returns a ParserFactoryImpl instance.

    Returns:
        A new ParserFactoryImpl instance.
    """
    return ParserFactoryImpl()
