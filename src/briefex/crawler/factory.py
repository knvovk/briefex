from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

from briefex.crawler.base import CrawlerFactory
from briefex.crawler.crawler import DefaultCrawler
from briefex.crawler.exceptions import CrawlerConfigurationError

if TYPE_CHECKING:
    from briefex.crawler import Crawler

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
        class_name = _default_crawler_cls.__name__
        _log.debug("Instantiating default crawler class '%s'", class_name)

        try:
            instance = _default_crawler_cls(*self._crawler_args, **self._crawler_kwargs)
            _log.info("Crawler '%s' instantiated successfully", class_name)
            return instance

        except Exception as exc:
            _log.error("Failed to instantiate crawler '%s': %s", class_name, exc)
            raise CrawlerConfigurationError(
                issue=f"Crawler instantiation failed for '{class_name}': {exc}",
                stage="crawler_instantiation",
            ) from exc
