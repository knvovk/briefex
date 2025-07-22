from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import override

from bs4 import BeautifulSoup, Tag

from briefex.crawler.exceptions import (
    ParseContentError,
    ParseError,
    ParseStructureError,
)
from briefex.crawler.models import PostDraft
from briefex.crawler.parsers.base import Parser

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
        _log.info("Parsing single article for %s", self._src)

        try:
            soup = self._get_soup(data)

            article = self._find_post_article(soup)
            if not article:
                selector = self._src.article_selector
                raise ParseStructureError(
                    issue=f"No article found with selector '{selector}'",
                    src_url=self._src.url,
                )

            return self._parse_post_article(article)

        except (ParseStructureError, ParseContentError, ParseError):
            raise

        except Exception as exc:
            _log.error("Unexpected error during parsing: %s", exc)
            raise ParseError(
                message=f"Unexpected error during parsing: {exc}",
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
        _log.info("Parsing multiple articles for %s", self._src)

        try:
            soup = self._get_soup(data)

            post_cards = self._find_post_cards(soup)
            if not post_cards:
                selector = self._src.card_selector
                raise ParseStructureError(
                    issue=f"No post cards found with selector '{selector}'",
                    src_url=self._src.url,
                )

            return self._parse_post_card_list(post_cards)

        except (ParseStructureError, ParseContentError, ParseError):
            raise

        except Exception as exc:
            _log.error("Unexpected error during parsing: %s", exc)
            raise ParseError(
                message=f"Unexpected error during parsing: {exc}",
                details={"src": self._src},
            ) from exc

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
            raise ParseContentError(
                issue="HTML content is empty",
                src_url=self._src.url,
            )

        try:
            html = data.decode(encoding=self._src.encoding, errors="replace")
            if not html.strip():
                raise ParseContentError(
                    issue="HTML content is empty",
                    src_url=self._src.url,
                )

            soup = BeautifulSoup(html, features="lxml")
            if not soup:
                raise ParseContentError(
                    issue="HTML content is empty",
                    src_url=self._src.url,
                )

            return soup

        except UnicodeDecodeError as exc:
            raise ParseContentError(
                issue=f"HTML content is invalid: {exc}",
                src_url=self._src.url,
            )

        except Exception as exc:
            _log.error("Failed to parse HTML content: %s", exc)
            raise ParseContentError(
                issue=f"HTML content is invalid: {exc}",
                src_url=self._src.url,
            )

    def _parse_post_card_list(self, post_cards: list[Tag]) -> list[PostDraft]:
        posts: list[PostDraft] = []
        for idx, post_card in enumerate(post_cards):
            try:
                post = self._parse_post_card(post_card)
                posts.append(post)
            except Exception as exc:
                _log.error(
                    "Failed to parse post card %d/%d: %s",
                    idx,
                    len(post_cards),
                    exc,
                )
                continue
        return posts
