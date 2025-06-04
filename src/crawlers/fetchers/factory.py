import logging
from typing import override

from .base import BaseFetcherFactory, BaseFetcher
from ..models import SourceType

logger = logging.getLogger(__name__)

_registry: dict[SourceType, type[BaseFetcher]] = {}


def register(src_type: SourceType):
    def _decorator(cls: type[BaseFetcher]):
        _registry[src_type] = cls
        logger.debug(
            "%s (fetcher) registered for %s",
            cls.__name__,
            src_type,
        )
        return cls

    return _decorator


class FetcherFactory(BaseFetcherFactory):

    def __init__(self) -> None:
        registered_fetchers = self.get_supported_fetchers()
        logger.info(
            "FetcherFactory initialized with %d registered fetchers: %s",
            len(registered_fetchers),
            ", ".join(registered_fetchers),
        )

    @override
    def create(self, src_type: SourceType, *args, **kwargs) -> BaseFetcher:
        logger.debug("Creating fetcher for %s", src_type)
        try:
            fetcher_cls = _registry[src_type]
            logger.debug("Found matching fetcher class: %s", fetcher_cls.__name__)
            fetcher = fetcher_cls(*args, **kwargs)
            logger.info("%s initialized for %s", fetcher.__class__.__name__, src_type)
            return fetcher
        except KeyError:
            registered_fetchers = self.get_supported_fetchers()
            error_msg = f"Unsupported source type: {src_type}"
            logger.error(
                "%s. Registered fetchers: %s",
                error_msg,
                ", ".join(registered_fetchers),
            )
            raise ValueError(error_msg) from None
        except Exception as exc:
            logger.exception(
                "Unexpected error creating fetcher for %s: %s",
                src_type,
                str(exc),
            )
            raise

    @staticmethod
    def get_supported_fetchers() -> list[SourceType]:
        return list(_registry.keys())
