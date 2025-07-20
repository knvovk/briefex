import briefex.crawler.fetchers.html  # noqa: F401
import briefex.crawler.fetchers.rss  # noqa: F401
from briefex.crawler.fetchers.base import Fetcher, FetcherFactory
from briefex.crawler.fetchers.factory import DefaultFetcherFactory

_fetcher_factory: FetcherFactory | None = None


def get_default_fetcher_factory() -> FetcherFactory:
    global _fetcher_factory

    if _fetcher_factory is None:
        _fetcher_factory = DefaultFetcherFactory()

    return _fetcher_factory


__all__ = ["Fetcher", "FetcherFactory", "get_default_fetcher_factory"]
