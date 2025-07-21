from __future__ import annotations

import logging
from collections.abc import Callable

from briefex.crawler.exceptions import CrawlerConfigurationError
from briefex.crawler.fetchers.base import Fetcher
from briefex.crawler.models import SourceType

_log = logging.getLogger(__name__)


class FetcherRegistry(dict[SourceType, type[Fetcher]]):
    """Map source types to their corresponding Fetcher subclasses."""

    def register(self, src_type: SourceType, cls: type[Fetcher]) -> None:
        """Register a Fetcher subclass for a given source type.

        Args:
            src_type: The SourceType key to associate.
            cls: The Fetcher subclass to register.

        Raises:
            CrawlerConfigurationError: If cls is not a subclass of Fetcher.
        """
        if not isinstance(cls, type) or not issubclass(cls, Fetcher):
            raise CrawlerConfigurationError(
                issue=f"Class `{cls.__name__}` must be a subclass of Fetcher",
                stage="fetcher_registration",
            )

        self[src_type] = cls
        _log.debug("%s registered for %s", cls.__name__, src_type)


fetcher_registry = FetcherRegistry()


def register(src_type: SourceType) -> Callable[[type[Fetcher]], type[Fetcher]]:
    """Create a decorator that registers a Fetcher for the given source type.

    Args:
        src_type: The SourceType under which to register the fetcher.

    Returns:
        A decorator that registers the decorated Fetcher subclass.
    """

    def wrapper(cls: type[Fetcher]) -> type[Fetcher]:
        """Register the decorated Fetcher class in the global registry.

        Args:
            cls: The Fetcher subclass to register.

        Returns:
            The original class.

        Raises:
            CrawlerConfigurationError: If registration fails.
        """
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
