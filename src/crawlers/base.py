import logging
from abc import ABC, abstractmethod

from .fetchers import BaseFetcherFactory, BaseFetcher
from .models import Source, Post, SourceType
from .parsers import BaseParser, BaseParserFactory

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):

    def __init__(
        self,
        fetcher_factory: BaseFetcherFactory,
        parser_factory: BaseParserFactory,
    ) -> None:
        self._fetcher_factory = fetcher_factory
        self._parser_factory = parser_factory
        self._fetchers: dict[SourceType, BaseFetcher] = {}
        self._parsers: dict[SourceType, BaseParser] = {}
        logger.info(
            "%s initialized with factories: fetcher=%s, parser=%s",
            self.__class__.__name__,
            fetcher_factory.__class__.__name__,
            parser_factory.__class__.__name__,
        )

    @abstractmethod
    def crawl(self, src: Source) -> list[Post]: ...

    def _get_fetcher(self, src: Source) -> BaseFetcher:
        if src.type not in self._fetchers:
            self._fetchers[src.type] = self._fetcher_factory.create(src.type)
        return self._fetchers[src.type]

    def _get_parser(self, src: Source) -> BaseParser:
        if src.type not in self._parsers:
            self._parsers[src.type] = self._parser_factory.create(src)
        return self._parsers[src.type]


class BaseCrawlerFactory(ABC):

    def __init__(self) -> None:
        logger.debug("CrawlerFactory initialized")

    @abstractmethod
    def create(
        self,
        fetcher_factory: BaseFetcherFactory,
        parser_factory: BaseParserFactory,
    ) -> BaseCrawler: ...
