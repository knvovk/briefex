import logging
from abc import ABC, abstractmethod
from typing import override

from .base import Crawler
from .crawler import CrawlerImpl
from .fetchers import FetcherFactory
from .parsers import ParserFactory

logger = logging.getLogger(__name__)


class CrawlerFactory(ABC):

    def __init__(self) -> None:
        logger.info("CrawlerFactory initialized")

    @abstractmethod
    def create(
        self,
        fetcher_factory: FetcherFactory,
        parser_factory: ParserFactory,
    ) -> Crawler: ...


class CrawlerFactoryImpl(CrawlerFactory):

    @override
    def create(
        self,
        fetcher_factory: FetcherFactory,
        parser_factory: ParserFactory,
    ) -> Crawler:
        return CrawlerImpl(fetcher_factory, parser_factory)


def create_crawler_factory() -> CrawlerFactory:
    return CrawlerFactoryImpl()
