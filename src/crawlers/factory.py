import logging
from typing import override

from .base import BaseCrawler, BaseCrawlerFactory
from .crawler import Crawler
from .fetchers import BaseFetcherFactory
from .parsers import BaseParserFactory

logger = logging.getLogger(__name__)


class CrawlerFactory(BaseCrawlerFactory):

    @property
    def default_crawler_cls(self) -> type:
        return Crawler

    @override
    def create(self, fetcher_factory: BaseFetcherFactory, parser_factory: BaseParserFactory) -> BaseCrawler:
        crawler = self.default_crawler_cls(fetcher_factory=fetcher_factory, parser_factory=parser_factory)
        return crawler
