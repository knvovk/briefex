import logging
from typing import Callable

from ..exceptions import CrawlerConfigurationError
from ..models import SourceType
from .base import Fetcher

logger = logging.getLogger(__name__)


class FetcherRegistry(dict[SourceType, type[Fetcher]]):

    def register(self, src_type: SourceType, cls: type[Fetcher]) -> None:
        self._validate_fetcher_class(cls)
        self[src_type] = cls
        logger.debug("%s registered for %s", cls.__name__, src_type)

    def _validate_fetcher_class(self, cls: type[Fetcher]) -> None:
        if not isinstance(cls, type) or not issubclass(cls, Fetcher):
            raise CrawlerConfigurationError(
                issue=f"Class {cls.__name__} must be a subclass of Fetcher",
                component="fetcher_registration",
            )

    def get_fetcher_names(self) -> list[str]:
        return [cls.__name__ for cls in self.values()]


fetcher_registry = FetcherRegistry()


def register(src_type: SourceType) -> Callable[[type[Fetcher]], type[Fetcher]]:
    def decorator(cls: type[Fetcher]) -> type[Fetcher]:
        try:
            fetcher_registry.register(src_type, cls)
            return cls
        except CrawlerConfigurationError:
            raise
        except Exception as exc:
            logger.error(
                "Failed to register fetcher %s for %s: %s",
                cls.__name__,
                src_type,
                exc,
            )
            raise CrawlerConfigurationError(
                issue=f"Registration failed for {cls.__name__}: {exc}",
                component="fetcher_registration",
            ) from exc

    return decorator
