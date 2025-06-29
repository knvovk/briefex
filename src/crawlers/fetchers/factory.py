import logging
from abc import ABC, abstractmethod
from typing import Callable, override

from ..exceptions import CrawlerConfigurationError
from ..models import SourceType
from .base import Fetcher

logger = logging.getLogger(__name__)

FetcherT = type[Fetcher]


class FetcherRegistry:

    def __init__(self) -> None:
        self._registry: dict[SourceType, FetcherT] = {}

    def register(self, src_type: SourceType, fetcher_class: FetcherT) -> None:
        self._validate_fetcher_class(fetcher_class)
        self._registry[src_type] = fetcher_class
        logger.debug("%s registered for %s", fetcher_class.__name__, src_type)

    def get(self, src_type: SourceType) -> FetcherT | None:
        return self._registry.get(src_type)

    def is_registered(self, src_type: SourceType) -> bool:
        return src_type in self._registry

    def get_registered_source_types(self) -> list[SourceType]:
        return list(self._registry.keys())

    def _validate_fetcher_class(self, fetcher_class: FetcherT) -> None:
        if not isinstance(fetcher_class, type) or not issubclass(
            fetcher_class, Fetcher
        ):
            raise CrawlerConfigurationError(
                issue=f"Class {fetcher_class.__name__} must be a subclass of Fetcher",
                component="fetcher_registration",
            )


_fetcher_registry = FetcherRegistry()


class FetcherFactory(ABC):

    def __init__(self, *args, **kwargs) -> None:
        self._args = args
        self._kwargs = kwargs

    @abstractmethod
    def create(self, src_type: SourceType) -> Fetcher: ...


class DefaultFetcherFactory(FetcherFactory):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._log_initialization()

    @override
    def create(self, src_type: SourceType) -> Fetcher:
        logger.debug("Initializing fetcher for %s", src_type)
        fetcher_class = self._get_fetcher_class(src_type)
        return self._instantiate_fetcher(fetcher_class, src_type)

    def _get_fetcher_class(self, src_type: SourceType) -> FetcherT:
        fetcher_class = _fetcher_registry.get(src_type)

        if fetcher_class is None:
            source_types = _fetcher_registry.get_registered_source_types()
            fetcher_list = [_fetcher_registry.get(t).__name__ for t in source_types]
            raise CrawlerConfigurationError(
                issue=f"No fetcher registered for {src_type}. "
                f"Registered fetchers: {', '.join(fetcher_list or 'None')}",
                component="fetcher_selection",
            )

        return fetcher_class

    def _instantiate_fetcher(
        self,
        fetcher_class: FetcherT,
        src_type: SourceType,
    ) -> Fetcher:
        try:
            fetcher = fetcher_class(*self._args, **self._kwargs)
            logger.info("%s initialized for %s", fetcher_class.__name__, src_type)
            return fetcher

        except Exception as exc:
            logger.error("Failed to instantiate %s: %s", fetcher_class.__name__, exc)
            raise CrawlerConfigurationError(
                issue=f"Fetcher instantiation failed for {fetcher_class.__name__}: {exc}",
                component="fetcher_instantiation",
            ) from exc

    def _log_initialization(self) -> None:
        source_types = _fetcher_registry.get_registered_source_types()
        fetcher_list = [_fetcher_registry.get(t).__name__ for t in source_types]
        logger.info(
            "FetcherFactory initialized with %d registered fetchers: %s",
            len(source_types),
            ", ".join(fetcher_list),
        )


def register(src_type: SourceType) -> Callable[[FetcherT], FetcherT]:
    def decorator(fetcher_class: FetcherT) -> FetcherT:
        try:
            _fetcher_registry.register(src_type, fetcher_class)
            return fetcher_class
        except Exception as exc:
            logger.error(
                "Failed to register fetcher %s for %s: %s",
                fetcher_class.__name__,
                src_type,
                exc,
            )
            raise CrawlerConfigurationError(
                issue=f"Registration failed for {fetcher_class.__name__}: {exc}",
                component="fetcher_registration",
            ) from exc

    return decorator


def create_default_fetcher_factory(*args, **kwargs) -> FetcherFactory:
    return DefaultFetcherFactory(*args, **kwargs)
