from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from briefex.crawler.exceptions import CrawlerConfigurationError
from briefex.crawler.fetchers.base import Fetcher
from briefex.crawler.models import SourceType

if TYPE_CHECKING:
    from collections.abc import Callable

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
            message = f"Cannot register '{cls.__name__}': not a Fetcher subclass"
            _log.error(message)
            raise CrawlerConfigurationError(
                issue=message,
                stage="fetcher_registration",
            )

        self[src_type] = cls
        _log.info(
            "Fetcher '%s' successfully registered for source type '%s'",
            cls.__name__,
            src_type,
        )


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
        _log.debug(
            "Attempting to register fetcher '%s' for source type '%s'",
            cls.__name__,
            src_type,
        )
        try:
            fetcher_registry.register(src_type, cls)
            _log.debug(
                "Registered fetcher '%s' for source type '%s'",
                cls.__name__,
                src_type,
            )
            return cls

        except CrawlerConfigurationError:
            raise

        except Exception as exc:
            _log.error(
                "Unexpected error registering fetcher '%s' for source type '%s': %s",
                cls.__name__,
                src_type,
                exc,
            )
            raise CrawlerConfigurationError(
                issue=f"Registration failed for '{cls.__name__}'",
                stage="fetcher_registration",
            ) from exc

    return wrapper
