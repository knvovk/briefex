import logging
from abc import ABC, abstractmethod
from typing import override

from .base import Crawler
from .crawler import CrawlerImpl
from .fetchers import FetcherFactory
from .parsers import ParserFactory

logger = logging.getLogger(__name__)


class CrawlerFactory(ABC):
    """Abstract base class for crawler factories.

    A crawler factory is responsible for creating crawler instances.
    Different implementations can create different types of crawlers.

    All crawler factories must implement the create method.
    """

    def __init__(
        self,
        fetcher_factory: FetcherFactory,
        parser_factory: ParserFactory,
    ) -> None:
        """Initialize a new CrawlerFactory.

        Args:
            fetcher_factory: The fetcher factory to use for creating fetchers.
            parser_factory: The parser factory to use for creating parsers.
        """
        self._fetcher_factory = fetcher_factory
        self._parser_factory = parser_factory
        logger.info("%s initialized", self.__class__.__name__)

    @abstractmethod
    def create(self) -> Crawler:
        """Create a new crawler.

        Returns:
            A new crawler instance.
        """
        ...


class CrawlerFactoryImpl(CrawlerFactory):
    """Implementation of the CrawlerFactory abstract class.

    This class provides a concrete implementation of the CrawlerFactory interface,
    creating CrawlerImpl instances.
    """

    @override
    def create(self) -> Crawler:
        """Create a new crawler.

        Creates a CrawlerImpl instance with the provided factories.

        Returns:
            A new CrawlerImpl instance.
        """
        return CrawlerImpl(self._fetcher_factory, self._parser_factory)


def create_crawler_factory(
    fetcher_factory: FetcherFactory,
    parser_factory: ParserFactory,
) -> CrawlerFactory:
    """Create a new crawler factory.

    This function is the main entry point for creating crawler factories.
    It creates and returns a CrawlerFactoryImpl instance.

    Args:
            fetcher_factory: The fetcher factory to use for creating fetchers.
            parser_factory: The parser factory to use for creating parsers.

    Returns:
        A new CrawlerFactoryImpl instance.
    """
    return CrawlerFactoryImpl(fetcher_factory, parser_factory)
