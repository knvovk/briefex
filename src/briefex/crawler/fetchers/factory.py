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
        _log.debug("Selecting fetcher for source type '%s'", src_type)
        if src_type not in fetcher_registry:
            message = f"No fetcher registered for source type '{src_type}'"
            _log.error(message)
            raise CrawlerConfigurationError(
                issue=message,
                stage="fetcher_selection",
            )

        fetcher_cls = fetcher_registry[src_type]
        try:
            instance = fetcher_cls(*self._fetcher_args, **self._fetcher_kwargs)
            _log.info(
                "Fetcher '%s' instantiated successfully for source type '%s'",
                fetcher_cls.__name__,
                src_type,
            )
            return instance

        except Exception as exc:
            _log.error(
                "Failed to instantiate fetcher '%s': %s",
                fetcher_cls.__name__,
                exc,
            )
            raise CrawlerConfigurationError(
                issue=f"Instantiation error in '{fetcher_cls.__name__}': {exc}",
                stage="fetcher_instantiation",
            ) from exc
