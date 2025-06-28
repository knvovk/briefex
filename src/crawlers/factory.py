import logging
from abc import ABC, abstractmethod
from typing import override

from .base import Crawler
from .crawler import DefaultCrawler
from .fetchers import FetcherFactory
from .parsers import ParserFactory

logger = logging.getLogger(__name__)


class CrawlerFactory(ABC):

    def __init__(self) -> None:
        logger.debug("CrawlerFactory initialized")

    @abstractmethod
    def create(
        self,
        fetcher_factory: FetcherFactory,
        parser_factory: ParserFactory,
    ) -> Crawler: ...


class DefaultCrawlerFactory(CrawlerFactory):

    @property
    def default_crawler_cls(self) -> type:
        return DefaultCrawler

    @override
    def create(
        self,
        fetcher_factory: FetcherFactory,
        parser_factory: ParserFactory,
    ) -> Crawler:
        crawler = self.default_crawler_cls(
            fetcher_factory=fetcher_factory,
            parser_factory=parser_factory,
        )
        return crawler


def create_default_crawler_factory() -> CrawlerFactory:
    return DefaultCrawlerFactory()
