from __future__ import annotations

import logging
import urllib.parse
from datetime import datetime
from typing import override

from bs4 import BeautifulSoup, Tag

from briefex.crawler.exceptions import ParseContentError, ParseError
from briefex.crawler.models import TIME_1970_01_01, PostDraft
from briefex.crawler.parsers.html import utils
from briefex.crawler.parsers.html.base import HTMLParser
from briefex.crawler.parsers.registry import register

_log = logging.getLogger(__name__)


@register("rt::html")
class RT(HTMLParser):
    """Parse RT HTML content into PostDraft objects."""

    @property
    def _article_selector(self) -> str:
        return "div.article_article-page"

    @property
    def _card_selector(self) -> str:
        return "div.listing__card"

    @property
    def _encoding(self) -> str:
        return "utf-8"

    @override
    def _find_post_cards(self, soup: BeautifulSoup) -> list[Tag]:
        cards = soup.find_all("div", class_="listing__card")
        _log.info(
            "Found %d post cards for source '%s'",
            len(cards),
            self._src.url,
        )
        return cards

    @override
    def _parse_post_card(self, card: Tag) -> PostDraft:
        _log.debug("Parsing post card element for source '%s'", self._src.url)
        heading_div = utils.find_required_tag(
            parent=card,
            name="div",
            cls="card__heading",
            netloc=utils.netloc(self._src.url),
        )
        title_link = utils.find_required_tag(
            parent=heading_div,
            name="a",
            cls="link",
            netloc=utils.netloc(self._src.url),
        )

        title = utils.clean_text(title_link.get_text())
        if not title.strip():
            _log.error("Empty title in post card for source '%s'", self._src.url)
            raise ParseContentError(
                issue="Post title is empty",
                src_url=self._src.url,
            )

        relative_url = utils.find_required_attr(
            tag=title_link,
            name="href",
            netloc=utils.netloc(self._src.url),
        )
        if not relative_url.strip():
            _log.error("Empty URL in post card for source '%s'", self._src.url)
            raise ParseContentError(
                issue="Post URL is empty",
                src_url=self._src.url,
            )

        absolute_url = urllib.parse.urljoin(self._src.url, relative_url)
        _log.debug("Post card parsed: title='%s', url='%s'", title, absolute_url)
        return PostDraft(title=title, canonical_url=absolute_url)

    @override
    def _find_post_article(self, soup: BeautifulSoup) -> Tag:
        article = soup.find("div", class_="article_article-page")
        if article is None:
            _log.error(
                "Article element not found using selector '%s' for source '%s'",
                self._article_selector,
                self._src.url,
            )
        else:
            _log.info("Article element found for source '%s'", self._src.url)
        return article

    @override
    def _parse_post_article(self, article: Tag) -> PostDraft:
        _log.debug("Parsing article content for source '%s'", self._src.url)
        article_div = utils.find_required_tag(
            parent=article,
            name="div",
            cls="article__text_article-page",
            netloc=utils.netloc(self._src.url),
        )

        paragraphs = article_div.find_all("p")
        raw_text = (
            "\n".join(p.get_text(strip=True) for p in paragraphs)
            if paragraphs
            else article_div.get_text(separator=" ", strip=True)
        )
        content = utils.clean_text(raw_text)

        try:
            time_tag = utils.find_required_tag(
                parent=article,
                name="time",
                cls="date",
                netloc=utils.netloc(self._src.url),
            )
            published_at_str = utils.find_required_attr(
                tag=time_tag,
                name="datetime",
                netloc=utils.netloc(self._src.url),
            )
            published_at = datetime.strptime(published_at_str, "%Y-%m-%d %H:%M")

            _log.debug(
                "Parsed publication date '%s' for source '%s'",
                published_at_str,
                self._src.url,
            )

        except (ParseError, ValueError) as exc:
            _log.warning(
                "Could not parse publication date for source '%s': %s; using epoch",
                self._src.url,
                exc,
            )
            published_at = TIME_1970_01_01

        _log.info(
            "Article parsed (length=%d chars) for source '%s'",
            len(content),
            self._src.url,
        )
        return PostDraft(content=content, published_at=published_at)
