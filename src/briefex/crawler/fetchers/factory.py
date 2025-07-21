from __future__ import annotations

import logging
from typing import override

from briefex.crawler.exceptions import CrawlerConfigurationError
from briefex.crawler.fetchers.base import Fetcher, FetcherFactory
from briefex.crawler.fetchers.registry import fetcher_registry
from briefex.crawler.models import SourceType

_log = logging.getLogger(__name__)


class DefaultFetcherFactory(FetcherFactory):
    """Factory that selects and instantiates fetchers from the registry."""

    @override
    def create(self, src_type: SourceType) -> Fetcher:
        """Instantiate a Fetcher for the given source type.

        Args:
            src_type: Source type for which to retrieve a fetcher.

        Returns:
            A Fetcher instance corresponding to the provided source type.

        Raises:
            CrawlerConfigurationError: If no fetcher is registered for src_type
                or if instantiation fails.
        """
        _log.debug("Initializing fetcher for %s", src_type)
        if src_type not in fetcher_registry:
            raise CrawlerConfigurationError(
                issue=f"No fetcher registered for {src_type}",
                stage="fetcher_selection",
            )

        fetcher_cls = fetcher_registry[src_type]
        try:
            instance = fetcher_cls(*self._fetcher_args, **self._fetcher_kwargs)
            _log.info("%s initialized for %s", fetcher_cls.__name__, src_type)
            return instance

        except Exception as exc:
            _log.error("Unexpected error during fetcher instantiation: %s", exc)
            raise CrawlerConfigurationError(
                issue=f"Fetcher instantiation failed for {fetcher_cls.__name__}: {exc}",
                stage="fetcher_instantiation",
            ) from exc
