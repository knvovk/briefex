from __future__ import annotations

import logging
from collections.abc import Callable

from briefex.crawler.exceptions import CrawlerConfigurationError
from briefex.crawler.fetchers.base import Fetcher
from briefex.crawler.models import SourceType

_log = logging.getLogger(__name__)


class FetcherRegistry(dict[SourceType, type[Fetcher]]):

    def register(self, src_type: SourceType, cls: type[Fetcher]) -> None:
        if not isinstance(cls, type) or not issubclass(cls, Fetcher):
            raise CrawlerConfigurationError(
                issue=f"Class `{cls.__name__}` must be a subclass of Fetcher",
                stage="fetcher_registration",
            )

        self[src_type] = cls
        _log.debug("%s registered for %s", cls.__name__, src_type)


fetcher_registry = FetcherRegistry()


def register(src_type: SourceType) -> Callable[[type[Fetcher]], type[Fetcher]]:
    def wrapper(cls: type[Fetcher]) -> type[Fetcher]:
        try:
            fetcher_registry.register(src_type, cls)
            return cls
        except CrawlerConfigurationError:
            raise
        except Exception as exc:
            _log.error("Unexpected error during fetcher registration: %s", exc)
            raise CrawlerConfigurationError(
                issue=f"`{cls.__name__}` registration failed",
                stage="fetcher_registration",
            ) from exc

    return wrapper
