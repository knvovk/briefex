import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import override
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel, ConfigDict

import utils

from ..exceptions import ParseContentError, ParseError, ParseStructureError
from ..models import PostDraft, Source
from .base import Parser
from .registry import register

logger = logging.getLogger(__name__)

NBSP_REGEX = re.compile(r"&nbsp;|\xa0")
WHITESPACE_REGEX = re.compile(r"\s+")

TIME_1970_01_01 = datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


def create_soup(html_content: str, url: str = "unknown") -> BeautifulSoup:
    """Create a BeautifulSoup object from HTML content.

    This function creates a BeautifulSoup object from HTML content,
    with error handling for empty content or parsing errors.

    Args:
        html_content: The HTML content to parse.
        url: The URL of the content, used for error reporting.

    Returns:
        A BeautifulSoup object representing the parsed HTML.

    Raises:
        ParseContentError: If the HTML content is empty.
        ParseStructureError: If a BeautifulSoup object cannot be created.
        ParseError: For other parsing errors.
    """
    if not html_content.strip():
        raise ParseContentError(
            url=url,
            parser_type="HTMLParser",
            reason="HTML content is empty",
        )

    try:
        soup = BeautifulSoup(html_content, features="lxml")
        if not soup:
            raise ParseStructureError(
                url=url,
                actual_value="Unable to create BeautifulSoup object from HTML content",
                expected_value="Valid HTML document",
            )
        return soup

    except Exception as exc:
        error_msg = f"Error creating BeautifulSoup object for {url}: {exc}"
        logger.error(error_msg)
        raise ParseError(error_msg) from exc


def find_required_tag(parent: Tag, name: str, class_: str, url: str = "unknown") -> Tag:
    """Find a required tag in a parent element.

    This function finds a tag with the specified name and class in a parent element,
    with error handling for missing parent or tag.

    Args:
        parent: The parent element to search in.
        name: The tag name to find.
        class_: The class name to find.
        url: The URL of the content, used for error reporting.

    Returns:
        The found tag.

    Raises:
        ParseStructureError: If the parent is None or the tag is not found.
    """
    if not parent:
        raise ParseStructureError(
            url=url,
            actual_value="None",
            expected_value=f"Parent element with selector '{name}'.'{class_}'",
        )

    tag = parent.find(name, class_=class_)
    if not tag:
        raise ParseStructureError(
            url=url,
            actual_value="None",
            expected_value=f"Tag '{name}' with class '{class_}'",
        )

    return tag


def get_required_attribute(tag: Tag, attr_name: str, url: str = "unknown") -> str:
    """Get a required attribute from a tag.

    This function gets an attribute with the specified name from a tag,
    with error handling for missing tag or attribute.

    Args:
        tag: The tag to get the attribute from.
        attr_name: The name of the attribute to get.
        url: The URL of the content, used for error reporting.

    Returns:
        The value of the attribute.

    Raises:
        ParseStructureError: If the tag is None or the attribute is not found.
    """
    if not tag:
        raise ParseStructureError(
            url=url,
            actual_value="None",
            expected_value=f"Tag with attribute '{attr_name}'",
        )

    attr = tag.get(attr_name)
    if not attr:
        raise ParseStructureError(
            url=url,
            actual_value=f"Attribute '{attr_name}' is empty",
            expected_value=f"Tag with attribute '{attr_name}'",
        )

    return attr


def clean_text(text: str | None) -> str:
    """Clean text by removing non-breaking spaces and normalizing whitespace.

    This function removes non-breaking spaces and normalizes whitespace in text.

    Args:
        text: The text to clean, or None.

    Returns:
        The cleaned text, or an empty string if the input is None or empty.
    """
    if not text:
        return ""

    cleaned = NBSP_REGEX.sub(" ", text)
    cleaned = WHITESPACE_REGEX.sub(" ", cleaned).strip()

    return cleaned


class Config(BaseModel):
    """Configuration for HTML parsers.

    This class defines the configuration parameters for HTML parsers,
    including tag names, class names, and datetime format.

    Attributes:
        article_tag: The tag name for article elements.
        article_cls: The class name for article elements.
        card_tag: The tag name for card elements.
        card_cls: The class name for card elements.
        datetime_fmt: The format string for parsing dates.
        encoding: The encoding to use for HTML content.
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    article_tag: str
    article_cls: str
    card_tag: str
    card_cls: str
    datetime_fmt: str
    encoding: str = "utf-8"


class HTMLParser(Parser, ABC):
    """Abstract base class for HTML parsers.

    This class provides a framework for parsing HTML content from sources.
    It handles common tasks like preparing the soup, finding and parsing
    post-cards and articles, and error handling.

    Subclasses must implement the abstract methods to provide source-specific
    parsing logic.

    Attributes:
        _config: Configuration for the parser.
        _domain: The domain of the source URL.
    """

    def __init__(self, src: Source) -> None:
        """Initialize a new HTMLParser.

        Args:
            src: The source to parse content for.
        """
        super().__init__(src)
        self._config = self._get_config()
        self._domain = utils.domain(src.url)

    @override
    def parse_one(self, data: bytes) -> PostDraft:
        """Parse a single post from HTML data.

        This method prepares the soup, finds the post-article, and parses it.

        Args:
            data: The raw HTML content to parse, as bytes.

        Returns:
            A PostDraft containing the extracted post-information.

        Raises:
            ParseContentError: If the HTML content is empty or cannot be decoded.
            ParseStructureError: If the article cannot be found.
            ParseError: For other parsing errors.
        """
        logger.info("Parsing single article for %s", self._src)

        try:
            soup = self._prepare_soup(data)
            article = self._find_post_article(soup)

            if not article:
                selector = f"{self._config.article_tag}.{self._config.article_cls}"
                raise ParseStructureError(
                    url=self._domain,
                    actual_value="None",
                    expected_value=f"Article with selector '{selector}'",
                )

            return self._parse_post_article(article)

        except (ParseError, ParseContentError, ParseStructureError):
            raise

        except Exception as exc:
            raise ParseError(
                f"Failed to parse single article for {self._src.name}: {exc}",
            )

    @override
    def parse_many(self, data: bytes) -> list[PostDraft]:
        """Parse multiple posts from HTML data.

        This method prepares the soup, finds post-cards, and parses each one.
        If a card fails to parse, it is skipped and the error is logged.

        Args:
            data: The raw HTML content to parse, as bytes.

        Returns:
            A list of PostDraft objects containing the extracted post-information.

        Raises:
            ParseContentError: If the HTML content is empty or cannot be decoded.
            ParseStructureError: If no post-cards can be found.
            ParseError: For other parsing errors.
        """
        logger.info("Parsing multiple articles for %s", self._src)

        try:
            soup = self._prepare_soup(data)
            cards = self._find_post_cards(soup)

            if not cards:
                selector = f"{self._config.card_tag}.{self._config.card_cls}"
                raise ParseStructureError(
                    url=self._domain,
                    actual_value="None",
                    expected_value=f"Post cards with selector '{selector}'",
                )

            posts: list[PostDraft] = []
            for i, card in enumerate(cards, 1):
                try:
                    post = self._parse_post_card(card)
                    posts.append(post)
                except Exception as exc:
                    logger.warning("Failed to parse card %d/%d: %s", i, len(cards), exc)
                    continue

            logger.info("Successfully parsed %d/%d articles", len(posts), len(cards))
            return posts

        except (ParseError, ParseContentError, ParseStructureError):
            raise

        except Exception as exc:
            raise ParseError(
                f"Failed to parse multiple articles for {self._src.name}: {exc}",
            )

    def _prepare_soup(self, data: bytes) -> BeautifulSoup:
        """Prepare a BeautifulSoup object from raw HTML data.

        This method decodes the HTML content using the configured encoding
        and creates a BeautifulSoup object.

        Args:
            data: The raw HTML content as bytes.

        Returns:
            A BeautifulSoup object representing the parsed HTML.

        Raises:
            ParseContentError: If the data is empty or cannot be decoded.
        """
        if not data:
            raise ParseContentError(
                url=self._domain,
                parser_type="HTMLParser",
                reason="HTML content is empty",
            )

        try:
            html_content = data.decode(encoding=self._config.encoding, errors="replace")
            return create_soup(html_content, self._domain)

        except UnicodeDecodeError as exc:
            raise ParseContentError(
                url=self._domain,
                parser_type="HTMLParser",
                reason=f"Error decoding HTML with {self._config.encoding}: {exc}",
            )

    @abstractmethod
    def _get_config(self) -> Config:
        """Get the configuration for this parser.

        Returns:
            A Config object with the parser configuration.
        """
        ...

    @abstractmethod
    def _find_post_cards(self, soup: BeautifulSoup) -> list[Tag]:
        """Find post-cards in the soup.

        Args:
            soup: The BeautifulSoup object to search in.

        Returns:
            A list of Tag objects representing post-cards.
        """
        ...

    @abstractmethod
    def _parse_post_card(self, card: Tag) -> PostDraft:
        """Parse a post-card into a PostDraft.

        Args:
            card: The Tag object representing a post-card.

        Returns:
            A PostDraft containing the extracted post-information.
        """
        ...

    @abstractmethod
    def _find_post_article(self, soup: BeautifulSoup) -> Tag:
        """Find a post-article in the soup.

        Args:
            soup: The BeautifulSoup object to search in.

        Returns:
            A Tag object representing the post-article.
        """
        ...

    @abstractmethod
    def _parse_post_article(self, article: Tag) -> PostDraft:
        """Parse a post-article into a PostDraft.

        Args:
            article: The Tag object representing a post-article.

        Returns:
            A PostDraft containing the extracted post-information.
        """
        ...


@register("rt_html")
class RT(HTMLParser):
    """Parser for RT (Russia Today) HTML content.

    This parser is responsible for parsing content from the RT website.
    It implements the abstract methods from HTMLParser to provide
    RT-specific parsing logic.
    """

    @override
    def _get_config(self) -> Config:
        """Get the configuration for the RT parser.

        Returns:
            A Config object with RT-specific configuration.
        """
        return Config(
            article_tag="div",
            article_cls="article_article-page",
            card_tag="div",
            card_cls="listing__card",
            datetime_fmt="%Y-%m-%d %H:%M",
        )

    @override
    def _find_post_cards(self, soup: BeautifulSoup) -> list[Tag]:
        """Find post-cards in the RT HTML soup.

        Args:
            soup: The BeautifulSoup object to search in.

        Returns:
            A list of Tag objects representing RT post-cards.
        """
        return soup.find_all(self._config.card_tag, class_=self._config.card_cls)

    @override
    def _parse_post_card(self, card: Tag) -> PostDraft:
        """Parse an RT post-card into a PostDraft.

        This method extracts the title and URL from the card
        and creates a PostDraft with these details.

        Args:
            card: The Tag object representing an RT post-card.

        Returns:
            A PostDraft containing the extracted post-information.
        """
        title, relative_url = self._extract_post_details(card)
        absolute_url = urljoin(self._src.url, relative_url)
        post_id = utils.normalize_id(
            relative_url.strip("/").split("/")[-1], self._src.code_name
        )

        return PostDraft(id=post_id, title=title, url=absolute_url)

    @override
    def _find_post_article(self, soup: BeautifulSoup) -> Tag:
        """Find a post-article in the RT HTML soup.

        Args:
            soup: The BeautifulSoup object to search in.

        Returns:
            A Tag object representing the RT post-article.
        """
        return soup.find(self._config.article_tag, class_=self._config.article_cls)

    @override
    def _parse_post_article(self, article: Tag) -> PostDraft:
        """Parse an RT post-article into a PostDraft.

        This method extracts the content and publication date from the article
        and creates a PostDraft with these details.

        Args:
            article: The Tag object representing an RT post-article.

        Returns:
            A PostDraft containing the extracted post-information.
        """
        content = self._extract_content(article)
        pub_date = self._extract_pub_date(article)

        return PostDraft(content=content, pub_date=pub_date)

    def _extract_post_details(self, card: Tag) -> tuple[str, str]:
        """Extract title and URL from an RT post-card.

        Args:
            card: The Tag object representing an RT post-card.

        Returns:
            A tuple containing the post-title and relative URL.

        Raises:
            ParseContentError: If the title or URL is empty.
        """
        heading_div = find_required_tag(card, "div", "card__heading", self._domain)
        title_link = find_required_tag(heading_div, "a", "link", self._domain)

        title = clean_text(title_link.get_text())
        if not title:
            raise ParseContentError(
                url=self._domain,
                parser_type="RT",
                reason="Post title is empty",
            )

        relative_url = get_required_attribute(title_link, "href", self._domain)
        if not relative_url.strip():
            raise ParseContentError(
                url=self._domain,
                parser_type="RT",
                reason="Post URL is empty",
            )

        return title, relative_url

    def _extract_content(self, article: Tag) -> str:
        """Extract content from an RT post-article.

        This method finds the article text div and extracts the content
        from paragraphs or the entire div if no paragraphs are found.

        Args:
            article: The Tag object representing an RT post-article.

        Returns:
            The extracted and cleaned content as a string.
        """
        article_div = find_required_tag(
            article,
            "div",
            "article__text_article-page",
            self._domain,
        )

        paragraphs = article_div.find_all("p")
        if paragraphs:
            raw_text = "\n".join(p.get_text(strip=True) for p in paragraphs)
        else:
            raw_text = article_div.get_text(separator=" ", strip=True)

        return clean_text(raw_text)

    def _extract_pub_date(self, article: Tag) -> datetime:
        """Extract publication date from an RT post-article.

        This method finds the time tag and extracts the datetime attribute.
        If parsing fails, it returns a default date (1970-01-01).

        Args:
            article: The Tag object representing an RT post-article.

        Returns:
            The extracted publication date as a datetime object,
            or a default date if parsing fails.
        """
        try:
            time_tag = find_required_tag(article, "time", "date", self._domain)
            pub_date_str = get_required_attribute(time_tag, "datetime", self._domain)

            return datetime.strptime(pub_date_str, self._config.datetime_fmt)

        except (ParseError, ValueError) as exc:
            logger.warning("Error parsing pub_date: %s", exc)
            return TIME_1970_01_01
