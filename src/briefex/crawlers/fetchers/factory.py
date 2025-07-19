import logging
from abc import ABC, abstractmethod
from typing import override

from ..exceptions import CrawlerConfigurationError
from ..models import SourceType
from .base import Fetcher
from .registry import fetcher_registry

logger = logging.getLogger(__name__)


class FetcherFactory(ABC):
    """Abstract base class for fetcher factories.

    A fetcher factory is responsible for creating fetcher instances.
    Different implementations can create different types of fetchers.

    All fetcher factories must implement the create method.

    Attributes:
        _args: Variable length argument list passed to fetchers.
        _kwargs: Arbitrary keyword arguments passed to fetchers.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initialize a new FetcherFactory.

        Args:
            *args: Variable length argument list to pass to fetchers.
            **kwargs: Arbitrary keyword arguments to pass to fetchers.
        """
        self._args = args
        self._kwargs = kwargs

    @abstractmethod
    def create(self, src_type: SourceType) -> Fetcher:
        """Create a new fetcher.

        Args:
            src_type: The type of source to create a fetcher for.

        Returns:
            A new fetcher instance.
        """
        ...


class FetcherFactoryImpl(FetcherFactory):
    """Implementation of the FetcherFactory abstract class.

    This class provides a concrete implementation of the FetcherFactory interface,
    creating fetchers based on the source type.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initialize a new FetcherFactoryImpl.

        Args:
            *args: Variable length argument list to pass to fetchers.
            **kwargs: Arbitrary keyword arguments to pass to fetchers.
        """
        super().__init__(*args, **kwargs)
        self._log_initialization()

    @override
    def create(self, src_type: SourceType) -> Fetcher:
        """Create a new fetcher.

        This method gets the appropriate fetcher class for the source type
        and instantiates it with the arguments provided to the factory.

        Args:
            src_type: The type of source to create a fetcher for.

        Returns:
            A new fetcher instance.

        Raises:
            CrawlerConfigurationError: If no fetcher is registered for the source type
                or if the fetcher instantiation fails.
        """
        logger.debug("Initializing fetcher for %s", src_type)
        cls = self._get_fetcher_class(src_type)
        return self._instantiate_fetcher(cls, src_type)

    def _get_fetcher_class(self, src_type: SourceType) -> type[Fetcher]:
        """Get the fetcher class for a source type.

        Args:
            src_type: The type of source to get a fetcher class for.

        Returns:
            The fetcher class for the source type.

        Raises:
            CrawlerConfigurationError: If no fetcher is registered for the source type.
        """
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

    def _instantiate_fetcher(self, cls: type[Fetcher], src_type: SourceType) -> Fetcher:
        """Instantiate a fetcher from a class.

        Args:
            cls: The fetcher class to instantiate.
            src_type: The type of source the fetcher is for.

        Returns:
            A new fetcher instance.

        Raises:
            CrawlerConfigurationError: If the fetcher instantiation fails.
        """
        try:
            fetcher = cls(*self._args, **self._kwargs)
            logger.info("%s initialized for %s", cls.__name__, src_type)
            return fetcher
        except Exception as exc:
            logger.error("Unexpected error during fetcher instantiation: %s", exc)
            raise CrawlerConfigurationError(
                issue=f"Fetcher instantiation failed for {cls.__name__}: {exc}",
                component="fetcher_instantiation",
            ) from exc

    def _log_initialization(self) -> None:
        """Log information about the initialized factory.

        This method logs the number and names of registered fetchers.
        """
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
    """Create a new fetcher factory.

    This function is the main entry point for creating fetcher factories.
    It creates and returns a FetcherFactoryImpl instance.

    Args:
        *args: Variable length argument list to pass to fetchers.
        **kwargs: Arbitrary keyword arguments to pass to fetchers.

    Returns:
        A new FetcherFactoryImpl instance.
    """
    return FetcherFactoryImpl(*args, **kwargs)
