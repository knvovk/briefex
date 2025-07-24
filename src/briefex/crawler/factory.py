from __future__ import annotations

import logging
from typing import override

from briefex.crawler import Crawler
from briefex.crawler.base import CrawlerFactory
from briefex.crawler.crawler import DefaultCrawler
from briefex.crawler.exceptions import CrawlerConfigurationError

_log = logging.getLogger(__name__)

_default_crawler_cls: type[Crawler] = DefaultCrawler


class DefaultCrawlerFactory(CrawlerFactory):
    """Factory that creates DefaultCrawler instances."""

    @override
    def create(self) -> Crawler:
        """Initialize and return the default Crawler instance.

        Raises:
            CrawlerConfigurationError: If crawler instantiation fails.
        """
        _log.debug("Initializing crawler by default: %s", _default_crawler_cls.__name__)
        try:
            instance = _default_crawler_cls(*self._crawler_args, **self._crawler_kwargs)
            _log.info(
                "%s initialized as default crawler",
                _default_crawler_cls.__name__,
            )
            return instance

        except Exception as exc:
            _log.error("Unexpected error during crawler initialization: %s", exc)
            cls = _default_crawler_cls.__name__
            raise CrawlerConfigurationError(
                issue=f"Crawler instantiation failed for {cls}: {exc}",
                stage="crawler_instantiation",
            ) from exc
