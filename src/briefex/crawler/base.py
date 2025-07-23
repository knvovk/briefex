from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from briefex.crawler.fetchers import FetcherFactory
from briefex.crawler.models import Post, Source
from briefex.crawler.parsers import ParserFactory

_log = logging.getLogger(__name__)


class Crawler(ABC):
    """Base class for crawlers that coordinate fetching and parsing."""

    def __init__(
        self,
        fetcher_factory: FetcherFactory,
        parser_factory: ParserFactory,
    ) -> None:
        self._fetcher_factory = fetcher_factory
        self._parser_factory = parser_factory

        _log.info(
            "%s initialized with fetcher_factory=%s, parser_factory=%s",
            self.__class__.__name__,
            fetcher_factory.__class__.__name__,
            parser_factory.__class__.__name__,
        )

    @abstractmethod
    def crawl(self, src: Source) -> list[Post]:
        """Crawl the given source to produce a list of posts.

        Args:
            src: Source configuration for the crawl.

        Returns:
            A list of Post objects extracted from the source.
        """
