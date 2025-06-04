import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import override
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

import utils
from .base import BaseParser
from .factory import register
from ..models import PostDraft

logger = logging.getLogger(__name__)

NBSP_REGEX = re.compile(r"&nbsp;|\xa0")

TIME_1970_01_01 = datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


def _get_soup(html_content: str) -> BeautifulSoup:
    length = utils.pretty_print_size(len(html_content))
    logger.debug("Creating BeautifulSoup object from HTML content (length=%s)", length)
    return BeautifulSoup(html_content, features="lxml")


def _get_required_tag(parent: Tag, name: str, class_: str, error_msg: str) -> Tag:
    logger.debug("Searching for required tag '%s.%s'", name, class_)
    tag = parent.find(name, class_=class_)
    if not tag:
        logger.error("Required tag '%s.%s' not found: %s", name, class_, error_msg)
        raise ValueError(error_msg)
    logger.debug("Successfully found required tag '%s.%s'", name, class_)
    return tag


def _get_required_attribute(tag: Tag, attr_name: str, error_msg: str) -> str:
    logger.debug(
        "Getting required attribute '%s' from tag '%s'",
        attr_name,
        tag.name or "unnamed tag",
    )
    attr = tag.get(attr_name)
    if not attr:
        logger.error(
            "Required attribute '%s' not found: %s",
            attr_name,
            error_msg,
        )
        raise ValueError(error_msg)
    logger.debug("Successfully retrieved attribute '%s' (length=%d)", attr_name, len(attr))
    return attr


def _clean_text(text: str | None) -> str:
    if not text:
        logger.debug("Empty text provided for cleaning, returning empty string")
        return ""
    text = NBSP_REGEX.sub(" ", text)
    cleaned_text = " ".join(text.split()).strip()
    cleaned_text = re.sub(r"\s+", " ", cleaned_text)
    logger.debug("Cleaning text: %d -> %d", len(text), len(cleaned_text))
    return cleaned_text


class HTMLParserConfig:

    def __init__(
        self,
        article_tag: str,
        article_cls: str,
        card_tag: str,
        card_cls: str,
        datetime_fmt: str,
        encoding: str = "utf-8",
    ) -> None:
        if not article_tag or not article_cls:
            error_msg = "article_tag and article_cls must be provided"
            logger.error("HTMLParserConfig validation failed: %s", error_msg)
            raise ValueError(error_msg)

        if not card_tag or not card_cls:
            error_msg = "card_tag and card_cls must be provided"
            logger.error("HTMLParserConfig validation failed: %s", error_msg)
            raise ValueError(error_msg)

        if not datetime_fmt:
            error_msg = "datetime_fmt must be provided"
            logger.error("HTMLParserConfig validation failed: %s", error_msg)
            raise ValueError(error_msg)

        self.article_tag = article_tag
        self.article_cls = article_cls
        self.card_tag = card_tag
        self.card_cls = card_cls
        self.datetime_fmt = datetime_fmt
        self.encoding = encoding

    def __repr__(self) -> str:
        return (
            "article_tag='%s', article_cls='%s', "
            "card_tag='%s', card_cls='%s', "
            "datetime_fmt='%s', encoding='%s'"
            % (
                self.article_tag,
                self.article_cls,
                self.card_tag,
                self.card_cls,
                self.datetime_fmt,
                self.encoding,
            )
        )

    def __str__(self) -> str:
        return repr(self)


class HTMLParser(BaseParser, ABC):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        try:
            self._config = self._get_config()
            logger.info(
                "%s parser initialized with %s",
                self.__class__.__name__,
                self._config,
            )
        except Exception as exc:
            logger.exception(
                "Unexpected error creating parser %s: %s",
                self.__class__.__name__,
                str(exc),
            )
            raise

    @override
    def parse_one(self, data: bytes) -> PostDraft:
        logger.info(
            "Starting parse_one for source '%s' (domain=%s, type=%s)",
            self._src.name,
            utils.domain(self._src.url),
            self._src.type,
        )
        try:
            html_content = self._prepare_html_content(data)
            soup = _get_soup(html_content)
            post_article = self._find_post_article(soup)
            if not post_article:
                article_selector = f"{self._config.article_tag}.{self._config.article_cls}"
                error_msg = f"No article '{article_selector}' found in HTML"
                raise ValueError(error_msg)
            post = self._parse_post_article(post_article)
            logger.info(
                "Finished parse_one for source '%s' (domain=%s, type=%s)",
                self._src.name,
                utils.domain(self._src.url),
                self._src.type,
            )
            return post
        except Exception as exc:
            logger.error(
                "Failed to parse_one for source '%s' (domain=%s, type=%s): %s",
                self._src.name,
                utils.domain(self._src.url),
                self._src.type,
                str(exc),
                exc_info=True,
            )
            raise

    @override
    def parse_many(self, data: bytes) -> list[PostDraft]:
        logger.info(
            "Starting parse_many for source '%s' (domain=%s, type=%s)",
            self._src.name,
            utils.domain(self._src.url),
            self._src.type,
        )
        try:
            html_content = self._prepare_html_content(data)
            soup = _get_soup(html_content)
            post_cards = self._find_post_cards(soup)
            if not post_cards:
                card_selector = f"{self._config.card_tag}.{self._config.card_cls}"
                error_msg = f"No cards '{card_selector}' found in HTML"
                raise ValueError(error_msg)
            posts: list[PostDraft] = []
            for idx, card in enumerate(post_cards):
                try:
                    logger.debug("Starting parse post card (%d/%d)", idx + 1, len(post_cards))
                    post = self._parse_post_card(card)
                    posts.append(post)
                    logger.debug("Successfully parsed post card (%d/%d)", idx + 1, len(post_cards))
                except Exception as exc:
                    logger.warning(
                        "Failed to parse post card (%d/%d): %s",
                        idx + 1,
                        len(post_cards),
                        str(exc),
                    )
                    continue
            logger.info(
                "Finished parse_many for source '%s' (domain=%s, type=%s)",
                self._src.name,
                utils.domain(self._src.url),
                self._src.type,
            )
            return posts
        except Exception as exc:
            logger.error(
                "Failed to parse_many for source '%s' (domain=%s, type=%s): %s",
                self._src.name,
                utils.domain(self._src.url),
                self._src.type,
                str(exc),
                exc_info=True,
            )
            raise

    def _prepare_html_content(self, data: bytes) -> str:
        encoding = self._config.encoding or "utf-8"
        logger.debug("Decoding HTML content with encoding: '%s'", encoding)
        try:
            html_content = data.decode(encoding=encoding, errors="replace")
            length = utils.pretty_print_size(len(html_content))
            logger.debug("Successfully decoded HTML content (length=%s)", length)
            return html_content
        except Exception as exc:
            logger.error("Failed to decode HTML content with %s encoding: %s", encoding, str(exc))
            raise

    @abstractmethod
    def _get_config(self) -> HTMLParserConfig: ...

    @abstractmethod
    def _find_post_cards(self, soup: BeautifulSoup) -> list[Tag]: ...

    @abstractmethod
    def _parse_post_card(self, card: Tag) -> PostDraft: ...

    @abstractmethod
    def _find_post_article(self, soup: BeautifulSoup) -> Tag: ...

    @abstractmethod
    def _parse_post_article(self, article: Tag) -> PostDraft: ...


@register("rt_html")
class RT(HTMLParser):

    @override
    def _get_config(self) -> HTMLParserConfig:
        return HTMLParserConfig(
            article_tag="div",
            article_cls="article_article-page",
            card_tag="div",
            card_cls="listing__card",
            datetime_fmt="%Y-%m-%d %H:%M",
        )

    @override
    def _find_post_cards(self, soup: BeautifulSoup) -> list[Tag]:
        logger.debug("Searching for post cards in HTML (class='%s')", self._config.card_cls)
        try:
            post_cards = soup.find_all(
                self._config.card_tag,
                class_=self._config.card_cls,
            )
            logger.info("Found %d post cards in HTML", len(post_cards))
            return post_cards
        except Exception as exc:
            logger.error("Failed to find post cards in HTML: %s", str(exc))
            raise

    @override
    def _parse_post_card(self, card: Tag) -> PostDraft:
        try:
            title, relative_url = self._extract_post_details_from_card(card)
            absolute_url = urljoin(self._src.url, relative_url)
            post_id_raw = relative_url.strip("/").split("/")[-1]
            post_id = utils.normalize_id(post_id_raw, self._src.code_name)
            draft = PostDraft(id=post_id, title=title, url=absolute_url)
            return draft
        except Exception as exc:
            error_msg = f"Error parsing post card: {exc}"
            logger.error(error_msg)
            raise ValueError(error_msg) from exc

    @override
    def _find_post_article(self, soup: BeautifulSoup) -> Tag:
        logger.debug("Searching for post article in HTML (class='%s')", self._config.article_cls)
        try:
            post_article = soup.find(self._config.article_tag, class_=self._config.article_cls)
            if post_article:
                logger.info("Found post article in HTML")
            return post_article
        except Exception as exc:
            logger.error("Failed to find post article in HTML: %s", str(exc))
            raise

    @override
    def _parse_post_article(self, article: Tag) -> PostDraft:
        try:
            content = self._extract_content_from_article(article)
            pub_date = self._extract_pub_date_from_article(article)
            draft = PostDraft(content=content, pub_date=pub_date)
            return draft
        except Exception as exc:
            error_msg = f"Error parsing post article: {exc}"
            logger.error(error_msg)
            raise ValueError(error_msg) from exc

    def _extract_post_details_from_card(self, card: Tag) -> tuple[str, str]:
        heading_div = _get_required_tag(card, "div", "card__heading", "Missing 'div.card__heading'")
        title_link = _get_required_tag(
            heading_div,
            "a",
            "link",
            "Missing 'a.link' in heading",
        )
        title_text = title_link.get_text(strip=True)
        title = " ".join(title_text.split())
        logger.debug("Post title extracted (length=%d)", len(title))
        relative_url = _get_required_attribute(title_link, "href", "Missing 'href' in 'a.link'")
        logger.debug("Post url extracted (length=%d)", len(relative_url))
        return title, relative_url

    def _extract_content_from_article(self, article: Tag) -> str:
        article_div = _get_required_tag(
            article,
            "div",
            "article__text_article-page",
            "Missing 'div.article__text_article-page'",
        )
        paragraphs = article_div.find_all("p")
        raw_text = ""
        if not paragraphs:
            logger.debug("No paragraphs found in article, using 'article_div.text' instead")
            raw_text = article_div.get_text(separator=" ", strip=True)
        else:
            for p in paragraphs:
                raw_text += p.get_text(strip=True) + "\n"
        cleaned_text = _clean_text(raw_text)
        logger.debug("Post content extracted (length=%d)", len(cleaned_text))
        return cleaned_text

    def _extract_pub_date_from_article(self, article: Tag) -> datetime:
        time_tag = _get_required_tag(
            article,
            "time",
            "date",
            "Missing 'time.date' in article",
        )
        pub_date_str = _get_required_attribute(
            time_tag,
            "datetime",
            "Missing 'datetime' in 'time.date'",
        )
        try:
            pub_date = datetime.strptime(pub_date_str, self._config.datetime_fmt)
            logger.debug("Post pub_date extracted: %s", pub_date)
            return pub_date
        except Exception as exc:
            logger.error("Error parsing post pub_date: %s", str(exc))
            return TIME_1970_01_01
