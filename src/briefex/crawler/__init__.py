from __future__ import annotations

from typing import Any

import briefex.crawler.crawler  # noqa: F401
from briefex.crawler.base import Crawler, CrawlerFactory
from briefex.crawler.exceptions import (
    CrawlerConfigurationError,
    CrawlerException,
    FetchConnectionError,
    FetchError,
    FetchHttpError,
    FetchTimeoutError,
    InvalidSourceError,
    ParseContentError,
    ParseError,
    ParseStructureError,
    SourceNotFoundError,
)
from briefex.crawler.factory import DefaultCrawlerFactory
from briefex.crawler.models import Post, PostDraft, Source, SourceType

_crawler_factory: CrawlerFactory | None = None


def get_default_crawler_factory(*args: Any, **kwargs: Any) -> CrawlerFactory:
    global _crawler_factory

    if _crawler_factory is None:
        _crawler_factory = DefaultCrawlerFactory(*args, **kwargs)

    return _crawler_factory


__all__ = [
    "Crawler",
    "CrawlerFactory",
    "CrawlerConfigurationError",
    "CrawlerException",
    "FetchConnectionError",
    "FetchError",
    "FetchHttpError",
    "FetchTimeoutError",
    "InvalidSourceError",
    "ParseContentError",
    "ParseError",
    "ParseStructureError",
    "SourceNotFoundError",
    "Post",
    "PostDraft",
    "Source",
    "SourceType",
    "get_default_crawler_factory",
]
