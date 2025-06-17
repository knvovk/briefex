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
from .base import BaseParser
from .factory import register

logger = logging.getLogger(__name__)

NBSP_REGEX = re.compile(r"&nbsp;|\xa0")
WHITESPACE_REGEX = re.compile(r"\s+")

TIME_1970_01_01 = datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


def create_soup(html_content: str, url: str = "unknown") -> BeautifulSoup:
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
                expected_structure="Valid HTML document",
                found_structure="Unable to create BeautifulSoup object from HTML content",
            )
        return soup

    except Exception as exc:
        error_msg = f"Error creating BeautifulSoup object for {url}: {exc}"
        logger.error(error_msg)
        raise ParseError(error_msg) from exc


def find_required_tag(parent: Tag, name: str, class_: str, url: str = "unknown") -> Tag:
    if not parent:
        raise ParseStructureError(
            url=url,
            expected_structure=f"Parent element with selector '{name}'.'{class_}'",
            found_structure="None",
        )

    tag = parent.find(name, class_=class_)
    if not tag:
        raise ParseStructureError(
            url=url,
            expected_structure=f"Tag '{name}' with class '{class_}'",
            found_structure="None",
        )

    return tag


def get_required_attribute(tag: Tag, attr_name: str, url: str = "unknown") -> str:
    if not tag:
        raise ParseStructureError(
            url=url,
            expected_structure=f"Tag with attribute '{attr_name}'",
            found_structure="None",
        )

    attr = tag.get(attr_name)
    if not attr:
        raise ParseStructureError(
            url=url,
            expected_structure=f"Tag with attribute '{attr_name}'",
            found_structure=f"Attribute '{attr_name}' is empty",
        )

    return attr


def clean_text(text: str | None) -> str:
    if not text:
        return ""

    cleaned = NBSP_REGEX.sub(" ", text)
    cleaned = WHITESPACE_REGEX.sub(" ", cleaned).strip()

    return cleaned


class HTMLParserConfig(BaseModel):

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


class HTMLParser(BaseParser, ABC):

    def __init__(self, src: Source) -> None:
        super().__init__(src)
        self._config = self._get_config()
        self._domain = utils.domain(src.url)
        logger.info(
            "%s parser initialized for %s",
            self.__class__.__name__,
            self._domain,
        )

    @override
    def parse_one(self, data: bytes) -> PostDraft:
        logger.info("Parsing single article for %s", self._domain)

        try:
            soup = self._prepare_soup(data)
            article = self._find_post_article(soup)

            if not article:
                selector = f"{self._config.article_tag}.{self._config.article_cls}"
                raise ParseStructureError(
                    url=self._domain,
                    expected_structure=f"Article with selector '{selector}'",
                    found_structure="None",
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
        logger.info("Parsing multiple articles for %s", self._domain)

        try:
            soup = self._prepare_soup(data)
            cards = self._find_post_cards(soup)

            if not cards:
                selector = f"{self._config.card_tag}.{self._config.card_cls}"
                raise ParseStructureError(
                    url=self._domain,
                    expected_structure=f"Post cards with selector '{selector}'",
                    found_structure="None",
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
        return soup.find_all(self._config.card_tag, class_=self._config.card_cls)

    @override
    def _parse_post_card(self, card: Tag) -> PostDraft:
        title, relative_url = self._extract_post_details(card)
        absolute_url = urljoin(self._src.url, relative_url)
        post_id = utils.normalize_id(
            relative_url.strip("/").split("/")[-1], self._src.code_name
        )

        return PostDraft(id=post_id, title=title, url=absolute_url)

    @override
    def _find_post_article(self, soup: BeautifulSoup) -> Tag:
        return soup.find(self._config.article_tag, class_=self._config.article_cls)

    @override
    def _parse_post_article(self, article: Tag) -> PostDraft:
        content = self._extract_content(article)
        pub_date = self._extract_pub_date(article)

        return PostDraft(content=content, pub_date=pub_date)

    def _extract_post_details(self, card: Tag) -> tuple[str, str]:
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
            raw_text = article_div.get_text(separator=" ", strip=True)  # noqa

        return clean_text(raw_text)

    def _extract_pub_date(self, article: Tag) -> datetime:
        """Извлекает дату публикации."""
        try:
            time_tag = find_required_tag(article, "time", "date", self._domain)
            pub_date_str = get_required_attribute(time_tag, "datetime", self._domain)

            return datetime.strptime(pub_date_str, self._config.datetime_fmt)

        except (ParseError, ValueError) as exc:
            logger.warning("Error parsing pub_date: %s", exc)
            return TIME_1970_01_01
