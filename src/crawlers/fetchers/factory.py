import logging
from typing import Callable, override

from ..exceptions import CrawlerConfigurationError, InvalidSourceError
from ..models import SourceType
from .base import BaseFetcher, BaseFetcherFactory

logger = logging.getLogger(__name__)

_registry: dict[SourceType, type[BaseFetcher]] = {}


def register(src_type: SourceType) -> Callable[[type[BaseFetcher]], type[BaseFetcher]]:

    def _decorator(cls: type[BaseFetcher]) -> type[BaseFetcher]:
        try:
            if not issubclass(cls, BaseFetcher):
                raise CrawlerConfigurationError(
                    issue=f"Class {cls.__name__} is not a subclass of BaseFetcher",
                    component="fetcher_registration",
                )

            _registry[src_type] = cls
            logger.debug("%s (fetcher) registered for %s", cls.__name__, src_type)
            return cls
        except Exception as exc:
            logger.error("Error registering fetcher %s for %s: %s", cls.__name__, src_type, exc)
            raise CrawlerConfigurationError(
                issue=f"Error registering fetcher {cls.__name__} for {src_type}: {exc}",
                component="fetcher_registration",
            ) from exc

    return _decorator


class FetcherFactory(BaseFetcherFactory):

    def __init__(self) -> None:
        try:
            registered_fetchers = self.get_registered_fetcher_types()
            logger.info(
                "FetcherFactory initialized with %d registered fetchers: %s",
                len(registered_fetchers),
                ", ".join(registered_fetchers),
            )
        except Exception as exc:
            logger.error("Error initializing FetcherFactory: %s", exc)
            raise CrawlerConfigurationError(
                issue=f"Error initializing FetcherFactory: {exc}", component="fetcher_factory_initialization"
            ) from exc

    @override
    def create(self, src_type: SourceType, *args, **kwargs) -> BaseFetcher:
        logger.debug("Creating fetcher for %s", src_type)
        if not src_type:
            raise InvalidSourceError(source_url="unknown", reason="Source type is not specified")

        try:
            if src_type not in _registry:
                registered_fetchers = self.get_registered_fetcher_types()
                error_msg = (
                    f"No fetcher registered for source type: {src_type}. "
                    f"Registered fetchers: {', '.join(registered_fetchers)}"
                )
                raise CrawlerConfigurationError(issue=error_msg, component="fetcher_selection")

            fetcher_cls = self.get_fetcher_class(src_type)
            logger.debug("Found matching fetcher class: %s", fetcher_cls.__name__)

            try:
                fetcher = fetcher_cls(*args, **kwargs)
                logger.info("%s initialized for %s", fetcher.__class__.__name__, src_type)
                return fetcher

            except Exception as exc:
                logger.error("Error instantiating fetcher %s: %s", fetcher_cls.__name__, exc)
                raise CrawlerConfigurationError(
                    issue=f"Error instantiating fetcher {fetcher_cls.__name__}: {exc}",
                    component="fetcher_instantiation",
                ) from exc

        except CrawlerConfigurationError:
            raise

        except Exception as exc:
            logger.exception("Unexpected error creating fetcher for %s: %s", src_type, str(exc))
            raise CrawlerConfigurationError(
                issue=f"Unexpected error creating fetcher for {src_type}: {exc}",
                component="fetcher_creation",
            ) from exc

    @staticmethod
    def get_registered_fetcher_types() -> list[SourceType]:
        return list(_registry.keys())

    @staticmethod
    def is_supported(src_type: SourceType) -> bool:
        return src_type in _registry

    @staticmethod
    def get_fetcher_class(src_type: SourceType) -> type[BaseFetcher] | None:
        try:
            return _registry.get(src_type)
        except Exception as exc:
            logger.error("Error getting fetcher class for %s: %s", src_type, exc)
            return None
