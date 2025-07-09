import logging
from typing import Callable

from ..exceptions import CrawlerConfigurationError
from ..models import SourceType
from .base import Fetcher

logger = logging.getLogger(__name__)


class FetcherRegistry(dict[SourceType, type[Fetcher]]):
    """Registry for fetcher classes.

    This class extends dict to provide a registry for fetcher classes,
    mapping source types to fetcher classes.
    """

    def register(self, src_type: SourceType, cls: type[Fetcher]) -> None:
        """Register a fetcher class for a source type.

        Args:
            src_type: The source type to register the fetcher for.
            cls: The fetcher class to register.

        Raises:
            CrawlerConfigurationError: If the class is not a valid fetcher class.
        """
        self._validate_fetcher_class(cls)
        self[src_type] = cls
        logger.debug("%s registered for %s", cls.__name__, src_type)

    def _validate_fetcher_class(self, cls: type[Fetcher]) -> None:
        """Validate that a class is a valid fetcher class.

        Args:
            cls: The class to validate.

        Raises:
            CrawlerConfigurationError: If the class is not a valid fetcher class.
        """
        if not isinstance(cls, type) or not issubclass(cls, Fetcher):
            raise CrawlerConfigurationError(
                issue=f"Class {cls.__name__} must be a subclass of Fetcher",
                component="fetcher_registration",
            )

    def get_fetcher_names(self) -> list[str]:
        """Get the names of all registered fetcher classes.

        Returns:
            A list of fetcher class names.
        """
        return [cls.__name__ for cls in self.values()]


fetcher_registry = FetcherRegistry()
"""Global registry for fetcher classes."""


def register(src_type: SourceType) -> Callable[[type[Fetcher]], type[Fetcher]]:
    """Decorator to register a fetcher class for a source type.

    This decorator registers a fetcher class with the global fetcher registry.

    Args:
        src_type: The source type to register the fetcher for.

    Returns:
        A decorator function that registers the decorated class.

    Example:
        @register(SourceType.HTML)
        class HTMLFetcher(Fetcher):
            ...
    """

    def decorator(cls: type[Fetcher]) -> type[Fetcher]:
        """Register a fetcher class and return it.

        Args:
            cls: The fetcher class to register.

        Returns:
            The registered fetcher class.

        Raises:
            CrawlerConfigurationError: If registration fails.
        """
        try:
            fetcher_registry.register(src_type, cls)
            return cls
        except CrawlerConfigurationError:
            raise
        except Exception as exc:
            logger.error("Unexpected error during fetcher registration: %s", exc)
            raise CrawlerConfigurationError(
                issue=f"Registration failed for {cls.__name__}: {exc}",
                component="fetcher_registration",
            ) from exc

    return decorator
