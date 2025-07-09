import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Summarizer(ABC):
    """Abstract base class for text summarizers.

    A summarizer is responsible for creating concise summaries of text content.
    All summarizers must implement the summarize method.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initialize a new Summarizer.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        ...

    @abstractmethod
    def summarize(self, text: str) -> str:
        """Summarize the given text.

        Args:
            text: The text to summarize.

        Returns:
            A concise summary of the input text.

        Raises:
            SummarizationError: If the text cannot be summarized.
        """
        ...
