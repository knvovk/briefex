import logging
from abc import ABC, abstractmethod
from typing import TypeVar

from .exceptions import CrawlerConfigurationError
from .fetchers import Fetcher, FetcherFactory
from .models import Post, Source
from .parsers import Parser, ParserFactory

logger = logging.getLogger(__name__)

T = TypeVar("T", Fetcher, Parser)


class ComponentManager[T]:
    """Manages components of a specific type.

    A generic class that manages components (Fetcher or Parser) by their keys.
    Components are created on demand and cached for reuse.

    Attributes:
        _components: Dictionary mapping keys to component instances.
        _component_type: String name of the component type for error messages.
    """

    def __init__(self, component_type: str):
        """Initialize a new ComponentManager.

        Args:
            component_type: String name of the component type for error messages.
        """
        self._components: dict[str, T] = {}
        self._component_type = component_type

    def get_or_create(self, key: str, factory_func) -> T:
        """Get an existing component or create a new one.

        If a component with the given key already exists, return it.
        Otherwise, create a new component using the factory function.

        Args:
            key: The key to identify the component.
            factory_func: A function that creates a new component.

        Returns:
            The component instance.

        Raises:
            CrawlerConfigurationError: If the factory function returns None.
        """
        if key not in self._components:
            component = factory_func()
            if component is None:
                raise CrawlerConfigurationError(
                    issue=f"No {self._component_type} registered for: {key}",
                    component=f"{self._component_type}_factory",
                )
            self._components[key] = component
        return self._components[key]


class Crawler(ABC):
    """Abstract base class for crawlers.

    A crawler is responsible for fetching and parsing content from sources.
    It uses fetcher and parser factories to create the appropriate components
    for each source.

    Attributes:
        _fetcher_factory: Factory for creating fetchers.
        _parser_factory: Factory for creating parsers.
        _fetcher_manager: Manager for fetcher components.
        _parser_manager: Manager for parser components.
    """

    def __init__(
        self,
        fetcher_factory: FetcherFactory,
        parser_factory: ParserFactory,
    ) -> None:
        """Initialize a new Crawler.

        Args:
            fetcher_factory: Factory for creating fetchers.
            parser_factory: Factory for creating parsers.
        """
        self._fetcher_factory = fetcher_factory
        self._parser_factory = parser_factory
        self._fetcher_manager = ComponentManager[Fetcher]("fetcher")
        self._parser_manager = ComponentManager[Parser]("parser")

        logger.info(
            "%s initialized with factories: %s, %s",
            self.__class__.__name__,
            fetcher_factory.__class__.__name__,
            parser_factory.__class__.__name__,
        )

    @abstractmethod
    def crawl(self, src: Source) -> list[Post]:
        """Crawl a source to extract posts.

        Args:
            src: The source to crawl.

        Returns:
            A list of extracted posts.
        """
        ...

    def _get_fetcher(self, src: Source) -> Fetcher:
        """Get a fetcher for a source.

        Args:
            src: The source to get a fetcher for.

        Returns:
            A fetcher for the source.

        Raises:
            CrawlerConfigurationError: If a fetcher cannot be created for the source.
        """
        try:
            return self._fetcher_manager.get_or_create(
                src.type.name,
                lambda: self._fetcher_factory.create(src.type),
            )
        except Exception as exc:
            logger.error(
                "Unexpected error getting fetcher for source %s: %s",
                src.name,
                exc,
            )
            raise CrawlerConfigurationError(
                issue=f"Error getting fetcher for source {src.name}: {exc}",
                component="fetcher_selection",
            ) from exc

    def _get_parser(self, src: Source) -> Parser:
        """Get a parser for a source.

        Args:
            src: The source to get a parser for.

        Returns:
            A parser for the source.

        Raises:
            CrawlerConfigurationError: If a parser cannot be created for the source.
        """
        try:
            return self._parser_manager.get_or_create(
                src.type.name,
                lambda: self._parser_factory.create(src),
            )
        except Exception as exc:
            logger.error(
                "Unexpected error getting parser for source %s: %s",
                src.name,
                exc,
            )
            raise CrawlerConfigurationError(
                issue=f"Error getting parser for source {src.name}: {exc}",
                component="parser_selection",
            ) from exc
