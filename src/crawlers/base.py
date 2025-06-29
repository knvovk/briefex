import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from .exceptions import CrawlerConfigurationError
from .fetchers import Fetcher, FetcherFactory
from .models import Post, Source
from .parsers import Parser, ParserFactory

logger = logging.getLogger(__name__)

T = TypeVar("T", Fetcher, Parser)


class ComponentManager(Generic[T]):

    def __init__(self, component_type: str):
        self._components: dict[str, T] = {}
        self._component_type = component_type

    def get_or_create(self, key: str, factory_func) -> T:
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

    def __init__(
        self,
        fetcher_factory: FetcherFactory,
        parser_factory: ParserFactory,
    ) -> None:
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
    def crawl(self, src: Source) -> list[Post]: ...

    def _get_fetcher(self, src: Source) -> Fetcher:
        try:
            return self._fetcher_manager.get_or_create(
                src.type.name,
                lambda: self._fetcher_factory.create(src.type),
            )
        except Exception as exc:
            logger.error("Error getting fetcher for source %s: %s", src.name, exc)
            raise CrawlerConfigurationError(
                issue=f"Error getting fetcher for source {src.name}: {exc}",
                component="fetcher_selection",
            ) from exc

    def _get_parser(self, src: Source) -> Parser:
        try:
            return self._parser_manager.get_or_create(
                src.type.name,
                lambda: self._parser_factory.create(src),
            )
        except Exception as exc:
            logger.error("Error getting parser for source %s: %s", src.name, exc)
            raise CrawlerConfigurationError(
                issue=f"Error getting parser for source {src.name}: {exc}",
                component="parser_selection",
            ) from exc
