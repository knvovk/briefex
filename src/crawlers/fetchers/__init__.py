from .base import Fetcher
from .factory import FetcherFactory, create_fetcher_factory
from .html import HTMLFetcher
from .rss import RSSFetcher

__all__ = ["Fetcher", "FetcherFactory", "create_fetcher_factory"]
