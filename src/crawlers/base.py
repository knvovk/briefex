import logging
from abc import ABC, abstractmethod

from .exceptions import CrawlerConfigurationError
from .fetchers import BaseFetcher, BaseFetcherFactory
from .models import Post, Source
from .parsers import BaseParser, BaseParserFactory

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):

    def __init__(self, fetcher_factory: BaseFetcherFactory, parser_factory: BaseParserFactory) -> None:
        self._fetcher_factory = fetcher_factory
        self._parser_factory = parser_factory
        self._fetchers: dict[str, BaseFetcher] = {}
        self._parsers: dict[str, BaseParser] = {}
        logger.info(
            "%s initialized with factories: fetcher=%s, parser=%s",
            self.__class__.__name__,
            fetcher_factory.__class__.__name__,
            parser_factory.__class__.__name__,
        )

    @abstractmethod
    def crawl(self, src: Source) -> list[Post]: ...

    def _get_fetcher(self, src: Source) -> BaseFetcher:
        try:
            if src.type.name not in self._fetchers:
                fetcher = self._fetcher_factory.create(src.type)

                if fetcher is None:
                    raise CrawlerConfigurationError(
                        issue=f"No fetcher registered for source type: {src.type.name}",
                        component="fetcher_factory",
                    )

                self._fetchers[src.type.name] = fetcher

            return self._fetchers[src.type.name]
        except Exception as exc:
            logger.error("Error getting fetcher for source %s: %s", src.name, exc)
            raise CrawlerConfigurationError(
                issue=f"Error getting fetcher for source {src.name}: {exc}",
                component="fetcher_selection",
            ) from exc

    def _get_parser(self, src: Source) -> BaseParser:
        try:
            if src.type.name not in self._parsers:
                parser = self._parser_factory.create(src)

                if parser is None:
                    raise CrawlerConfigurationError(
                        issue=f"No parser registered for source type: {src.type.name}",
                        component="parser_factory",
                    )

                self._parsers[src.type.name] = parser

            return self._parsers[src.type.name]

        except Exception as exc:
            logger.error("Error getting parser for source %s: %s", src.name, exc)
            raise CrawlerConfigurationError(
                issue=f"Error getting parser for source {src.name}: {exc}",
                component="parser_selection",
            ) from exc


class BaseCrawlerFactory(ABC):

    def __init__(self) -> None:
        logger.debug("CrawlerFactory initialized")

    @abstractmethod
    def create(self, fetcher_factory: BaseFetcherFactory, parser_factory: BaseParserFactory) -> BaseCrawler: ...
