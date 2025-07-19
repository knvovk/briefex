import logging
from abc import ABC, abstractmethod

from ..models import PostDraft, Source

logger = logging.getLogger(__name__)


class Parser(ABC):
    """Abstract base class for parsers.

    A parser is responsible for parsing content from a source and extracting posts.
    Different implementations can handle different types of sources.

    All parsers must implement the parse_one and parse_many methods.

    Attributes:
        _src: The source that this parser is configured for.
    """

    def __init__(self, src: Source) -> None:
        """Initialize a new Parser.

        Args:
            src: The source that this parser will parse content for.
        """
        self._src = src

    @abstractmethod
    def parse_one(self, data: bytes) -> PostDraft:
        """Parse a single post from the provided data.

        This method is typically used to parse an individual post-page.

        Args:
            data: The raw content to parse, as bytes.

        Returns:
            A PostDraft containing the extracted post-information.

        Raises:
            ParseError: If the content cannot be parsed.
        """
        ...

    @abstractmethod
    def parse_many(self, data: bytes) -> list[PostDraft]:
        """Parse multiple posts from the provided data.

        This method is typically used to parse a list of posts from a main page.

        Args:
            data: The raw content to parse, as bytes.

        Returns:
            A list of PostDraft objects containing the extracted post-information.

        Raises:
            ParseError: If the content cannot be parsed.
        """
        ...
