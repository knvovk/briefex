import logging
from abc import ABC, abstractmethod
from typing import override

from ..exceptions import CrawlerConfigurationError
from ..models import SourceType
from .base import Fetcher
from .registry import fetcher_registry

logger = logging.getLogger(__name__)

FetcherT = type[Fetcher]


class FetcherFactory(ABC):

    def __init__(self, *args, **kwargs) -> None:
        self._args = args
        self._kwargs = kwargs

    @abstractmethod
    def create(self, src_type: SourceType) -> Fetcher: ...


class FetcherFactoryImpl(FetcherFactory):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._log_initialization()

    @override
    def create(self, src_type: SourceType) -> Fetcher:
        logger.debug("Initializing fetcher for %s", src_type)
        cls = self._get_fetcher_class(src_type)
        return self._instantiate_fetcher(cls, src_type)

    def _get_fetcher_class(self, src_type: SourceType) -> FetcherT:
        if src_type not in fetcher_registry:
            available_fetchers = fetcher_registry.get_fetcher_names()
            fetchers_str = (
                ", ".join(available_fetchers) if available_fetchers else "None"
            )
            raise CrawlerConfigurationError(
                issue=f"No fetcher registered for {src_type}. "
                f"Available fetchers: {fetchers_str}",
                component="fetcher_selection",
            )

        return fetcher_registry[src_type]

    def _instantiate_fetcher(self, cls: FetcherT, src_type: SourceType) -> Fetcher:
        try:
            fetcher = cls(*self._args, **self._kwargs)
            logger.info("%s initialized for %s", cls.__name__, src_type)
            return fetcher
        except Exception as exc:
            logger.error("Failed to instantiate %s: %s", cls.__name__, exc)
            raise CrawlerConfigurationError(
                issue=f"Fetcher instantiation failed for {cls.__name__}: {exc}",
                component="fetcher_instantiation",
            ) from exc

    def _log_initialization(self) -> None:
        fetcher_count = len(fetcher_registry)
        if fetcher_count == 0:
            logger.warning("FetcherFactory initialized with no registered fetchers")
            return

        fetcher_names = fetcher_registry.get_fetcher_names()
        logger.info(
            "FetcherFactory initialized with %d fetcher%s: %s",
            fetcher_count,
            "s" if fetcher_count > 1 else "",
            ", ".join(fetcher_names),
        )


def create_fetcher_factory(*args, **kwargs) -> FetcherFactory:
    return FetcherFactoryImpl(*args, **kwargs)
