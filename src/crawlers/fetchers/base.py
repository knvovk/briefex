import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Fetcher(ABC):
    """Abstract base class for fetchers.

    A fetcher is responsible for retrieving content from a URL.
    Different implementations can handle different types of sources.

    All fetchers must implement the fetch and close methods.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initialize a new Fetcher.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        ...

    @abstractmethod
    def fetch(self, url: str) -> bytes:
        """Fetch content from a URL.

        Args:
            url: The URL to fetch content from.

        Returns:
            The fetched content as bytes.

        Raises:
            FetchError: If the content cannot be fetched.
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """Close the fetcher and release any resources.

        This method should be called when the fetcher is no longer needed.
        """
        ...
