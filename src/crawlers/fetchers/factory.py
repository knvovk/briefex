import logging
from abc import ABC, abstractmethod
from typing import Callable, override

from ..exceptions import CrawlerConfigurationError
from ..models import SourceType
from .base import BaseFetcher

logger = logging.getLogger(__name__)


class FetcherRegistry:

    def __init__(self) -> None:
        self._registry: dict[SourceType, type[BaseFetcher]] = {}

    def register(
        self,
        source_type: SourceType,
        fetcher_class: type[BaseFetcher],
    ) -> None:
        self._validate_fetcher_class(fetcher_class)
        self._registry[source_type] = fetcher_class
        logger.debug(
            "Registered %s for source type %s",
            fetcher_class.__name__,
            source_type,
        )

    def get(self, source_type: SourceType) -> type[BaseFetcher] | None:
        return self._registry.get(source_type)

    def is_registered(self, source_type: SourceType) -> bool:
        return source_type in self._registry

    def get_registered_types(self) -> list[SourceType]:
        return list(self._registry.keys())

    def _validate_fetcher_class(self, fetcher_class: type[BaseFetcher]) -> None:  # noqa
        if not isinstance(fetcher_class, type) or not issubclass(
            fetcher_class, BaseFetcher
        ):
            raise CrawlerConfigurationError(
                issue=f"Class {fetcher_class.__name__} must be a subclass of BaseFetcher",
                component="fetcher_registration",
            )


_fetcher_registry = FetcherRegistry()


def register(
    source_type: SourceType,
) -> Callable[[type[BaseFetcher]], type[BaseFetcher]]:
    def decorator(fetcher_class: type[BaseFetcher]) -> type[BaseFetcher]:
        try:
            _fetcher_registry.register(source_type, fetcher_class)
            return fetcher_class
        except Exception as exc:
            logger.error(
                "Failed to register fetcher %s for %s: %s",
                fetcher_class.__name__,
                source_type,
                exc,
            )
            raise CrawlerConfigurationError(
                issue=f"Registration failed for {fetcher_class.__name__}: {exc}",
                component="fetcher_registration",
            ) from exc

    return decorator


class BaseFetcherFactory(ABC):

    def __init__(self, *args, **kwargs) -> None:
        self._args = args
        self._kwargs = kwargs

    @abstractmethod
    def create(self, src_type: SourceType) -> BaseFetcher: ...


class FetcherFactory(BaseFetcherFactory):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._log_initialization()

    @override
    def create(self, source_type: SourceType) -> BaseFetcher:
        logger.debug("Creating fetcher for source type: %s", source_type)

        fetcher_class = self._get_fetcher_class(source_type)
        return self._instantiate_fetcher(fetcher_class, source_type)

    def _get_fetcher_class(self, source_type: SourceType) -> type[BaseFetcher]:  # noqa
        fetcher_class = _fetcher_registry.get(source_type)

        if fetcher_class is None:
            registered_types = [
                str(t) for t in _fetcher_registry.get_registered_types()
            ]
            raise CrawlerConfigurationError(
                issue=(
                    f"No fetcher registered for source type '{source_type}'. "
                    f"Available types: {', '.join(registered_types) or 'none'}"
                ),
                component="fetcher_selection",
            )
        return fetcher_class

    def _instantiate_fetcher(
        self,
        fetcher_class: type[BaseFetcher],
        source_type: SourceType,
    ) -> BaseFetcher:
        try:
            fetcher = fetcher_class(*self._args, **self._kwargs)
            logger.info(
                "Successfully created %s for source type %s",
                fetcher_class.__name__,
                source_type,
            )
            return fetcher

        except Exception as exc:
            logger.error("Failed to instantiate %s: %s", fetcher_class.__name__, exc)
            raise CrawlerConfigurationError(
                issue=f"Fetcher instantiation failed for {fetcher_class.__name__}: {exc}",
                component="fetcher_instantiation",
            ) from exc

    def _log_initialization(self) -> None:  # noqa
        registered_types = _fetcher_registry.get_registered_types()
        logger.info(
            "FetcherFactory initialized with %d registered fetchers: %s",
            len(registered_types),
            ", ".join(str(t) for t in registered_types),
        )
