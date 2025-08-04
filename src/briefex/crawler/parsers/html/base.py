from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, override

from bs4 import BeautifulSoup, Tag

from briefex.crawler.exceptions import (
    ParseContentError,
    ParseError,
    ParseStructureError,
)
from briefex.crawler.parsers.base import Parser

if TYPE_CHECKING:
    from briefex.crawler.models import PostDraft

_log = logging.getLogger(__name__)


class HTMLParser(Parser, ABC):
    """Base parser for extracting one or more posts from HTML content."""

    @override
    def parse(self, data: bytes) -> PostDraft:
        """Parse HTML bytes to a single PostDraft.

        Args:
            data: Raw HTML bytes to parse.

        Returns:
            A PostDraft representing the parsed article.

        Raises:
            ParseStructureError: If the article element is missing.
            ParseContentError: If the HTML content is empty or invalid.
            ParseError: On unexpected parsing errors.
        """
        _log.info("Parsing single article for source '%s'", self._src.url)

        try:
            soup = self._get_soup(data)

            article = self._find_post_article(soup)
            if not article:
                selector = self._article_selector
                message = f"No article found using selector '{selector}'"
                _log.error("%s for URL '%s'", message, self._src.url)
                raise ParseStructureError(issue=message, src_url=self._src.url)

            return self._parse_post_article(article)

        except (ParseStructureError, ParseContentError, ParseError):
            raise

        except Exception as exc:
            _log.error(
                "Parsing failed unexpectedly for URL '%s': %s",
                self._src.url,
                exc,
            )
            raise ParseError(
                message=f"Unexpected parsing error: {exc}",
                details={"src": self._src},
            ) from exc

    @override
    def parse_many(self, data: bytes) -> list[PostDraft]:
        """Parse HTML bytes to multiple PostDrafts.

        Args:
            src: Source configuration with selectors and encoding.
            data: Raw HTML bytes to parse.

        Returns:
            A list of PostDrafts for each parsed post card.

        Raises:
            ParseStructureError: If no post cards are found.
            ParseContentError: If the HTML content is empty or invalid.
            ParseError: On unexpected parsing errors.
        """
        _log.info("Parsing multiple articles for source '%s'", self._src.url)

        try:
            soup = self._get_soup(data)

            post_cards = self._find_post_cards(soup)
            if not post_cards:
                selector = self._card_selector
                message = f"No post cards found using selector '{selector}'"
                _log.error("%s for URL '%s'", message, self._src.url)
                raise ParseStructureError(issue=message, src_url=self._src.url)

            return self._parse_post_card_list(post_cards)

        except (ParseStructureError, ParseContentError, ParseError):
            raise

        except Exception as exc:
            _log.error(
                "Parsing of multiple articles failed unexpectedly for URL '%s': %s",
                self._src.url,
                exc,
            )
            raise ParseError(
                message=f"Unexpected parsing error: {exc}",
                details={"src": self._src},
            ) from exc

    @property
    @abstractmethod
    def _article_selector(self) -> str:
        """CSS selector used to locate the main article element."""

    @property
    @abstractmethod
    def _card_selector(self) -> str:
        """CSS selector used to locate post card elements."""

    @property
    @abstractmethod
    def _encoding(self) -> str:
        """Character encoding used to decode HTML bytes."""

    @abstractmethod
    def _find_post_cards(self, soup: BeautifulSoup) -> list[Tag]:
        """Locate post card elements in the parsed HTML."""

    @abstractmethod
    def _parse_post_card(self, card: Tag) -> PostDraft:
        """Extract a PostDraft from a single post card element."""

    @abstractmethod
    def _find_post_article(self, soup: BeautifulSoup) -> Tag:
        """Locate the main article element in the parsed HTML."""

    @abstractmethod
    def _parse_post_article(self, article: Tag) -> PostDraft:
        """Extract a PostDraft from a single article element."""

    def _get_soup(self, data: bytes) -> BeautifulSoup:
        if not data:
            message = "HTML content is empty"
            _log.error("%s for source '%s'", message, self._src.url)
            raise ParseContentError(issue=message, src_url=self._src.url)

        try:
            html = data.decode(encoding=self._encoding, errors="replace")
            if not html.strip():
                message = "HTML content is empty after decoding"
                _log.error("%s for source '%s'", message, self._src.url)
                raise ParseContentError(issue=message, src_url=self._src.url)

            soup = BeautifulSoup(html, features="lxml")
            if not soup:
                message = "Failed to create BeautifulSoup object"
                _log.error("%s for source '%s'", message, self._src.url)
                raise ParseContentError(issue=message, src_url=self._src.url)

            return soup

        except UnicodeDecodeError as exc:
            message = f"HTML decoding error: {exc}"
            _log.error("%s for source '%s'", message, self._src.url)
            raise ParseContentError(
                issue=message,
                src_url=self._src.url,
            ) from exc

        except Exception as exc:
            _log.error("HTML parsing error for source '%s': %s", self._src.url, exc)
            raise ParseContentError(
                issue=f"Invalid HTML content: {exc}",
                src_url=self._src.url,
            ) from exc

    def _parse_post_card_list(self, post_cards: list[Tag]) -> list[PostDraft]:
        posts: list[PostDraft] = []
        total = len(post_cards)
        for idx, post_card in enumerate(post_cards, start=1):
            try:
                post = self._parse_post_card(post_card)
                post.source = self._src if not post.source else post.source
                posts.append(post)
                _log.debug("Parsed post card %d/%d successfully", idx, total)
            except Exception as exc:
                _log.error(
                    "Failed to parse post card %d/%d for source '%s': %s",
                    idx,
                    total,
                    self._src.url,
                    exc,
                )
        return posts
