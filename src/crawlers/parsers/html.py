import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import override
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

import utils

from ..exceptions import CrawlerConfigurationError, ParseContentError, ParseError, ParseStructureError
from ..models import PostDraft, Source
from .base import BaseParser
from .factory import register

logger = logging.getLogger(__name__)

NBSP_REGEX = re.compile(r"&nbsp;|\xa0")

TIME_1970_01_01 = datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


def _get_soup(html_content: str, url: str = "unknown") -> BeautifulSoup:
    try:
        length = utils.pretty_print_size(len(html_content))
        logger.debug("Creating BeautifulSoup object from HTML content (length=%s)", length)

        if not html_content.strip():
            raise ParseContentError(
                url=url,
                parser_type="HTMLParser",
                reason="HTML content is empty",
            )

        soup = BeautifulSoup(html_content, features="lxml")
        if not soup:
            raise ParseStructureError(
                url=url,
                expected_structure="Valid HTML document",
                found_structure="Unable to create BeautifulSoup object from HTML content",
            )

        return soup

    except ParseError:
        raise

    except Exception as exc:
        error_msg = f"Error creating BeautifulSoup object for {url}: {exc}"
        logger.error(error_msg)
        raise ParseError(error_msg) from exc


def _get_required_tag(parent: Tag, name: str, class_: str, url: str = "unknown") -> Tag:
    try:
        logger.debug("Searching for required tag '%s.%s'", name, class_)

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

        logger.debug("Successfully found required tag '%s.%s'", name, class_)
        return tag
    except ParseError:
        raise

    except Exception as exc:
        error_msg = f"Error finding required tag '{name}.{class_}' for {url}: {exc}"
        logger.error(error_msg)
        raise ParseError(error_msg) from exc


def _get_required_attribute(tag: Tag, attr_name: str, url: str = "unknown") -> str:
    try:
        logger.debug("Getting required attribute '%s' from tag '%s'", attr_name, tag.name)

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

        logger.debug("Successfully retrieved attribute '%s' (length=%d)", attr_name, len(attr))
        return attr

    except ParseError:
        raise

    except Exception as exc:
        error_msg = f"Error getting required attribute '{attr_name}' from tag in {url}: {exc}"
        logger.error(error_msg)
        raise ParseError(error_msg) from exc


def _clean_text(text: str | None, url: str = "unknown") -> str:
    try:
        if not text:
            logger.debug("Empty text provided for cleaning, returning empty string")
            return ""

        text = NBSP_REGEX.sub(" ", text)

        cleaned_text = " ".join(text.split()).strip()
        cleaned_text = re.sub(r"\s+", " ", cleaned_text)

        logger.debug("Cleaning text: %d -> %d", len(text), len(cleaned_text))
        return cleaned_text

    except Exception as exc:
        error_msg = f"Error cleaning text for {url}: {exc}"
        logger.error(error_msg)
        raise ParseError(error_msg) from exc


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
        try:
            if not article_tag or not article_tag.strip():
                raise CrawlerConfigurationError(
                    issue="article_tag must not be empty",
                    component="html_parser_config",
                )

            if not article_cls or not article_cls.strip():
                raise CrawlerConfigurationError(
                    issue="article_cls must not be empty",
                    component="html_parser_config",
                )

            if not card_tag or not card_tag.strip():
                raise CrawlerConfigurationError(
                    issue="card_tag must not be empty",
                    component="html_parser_config",
                )

            if not card_cls or not card_cls.strip():
                raise CrawlerConfigurationError(
                    issue="card_cls must not be empty",
                    component="html_parser_config",
                )

            if not datetime_fmt or not datetime_fmt.strip():
                raise CrawlerConfigurationError(
                    issue="datetime_fmt must not be empty",
                    component="html_parser_config",
                )

            self.article_tag = article_tag.strip()
            self.article_cls = article_cls.strip()
            self.card_tag = card_tag.strip()
            self.card_cls = card_cls.strip()
            self.datetime_fmt = datetime_fmt.strip()
            self.encoding = encoding.strip() if encoding else "utf-8"

        except CrawlerConfigurationError:
            raise

        except Exception as exc:
            logger.error("Error creating HTMLParserConfig: %s", exc)
            raise CrawlerConfigurationError(
                issue=f"Error creating HTMLParserConfig: {exc}",
                component="html_parser_config",
            ) from exc

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

    def __init__(self, src: Source, *args, **kwargs) -> None:
        try:
            super().__init__(src, *args, **kwargs)
            self._src = src
            self._config = self._get_config()
            logger.info(
                "%s parser initialized with %s",
                self.__class__.__name__,
                self._config,
            )
        except Exception as exc:
            logger.exception("Unexpected error creating parser %s: %s", self.__class__.__name__, exc)
            raise CrawlerConfigurationError(
                issue=f"Unexpected error creating parser {self.__class__.__name__}: {exc}",
                component="html_parser_initialization",
            )

    @override
    def parse_one(self, data: bytes) -> PostDraft:
        logger.info(
            "Starting parse_one for source '%s' (domain=%s, type=%s)",
            self._src.name,
            self._get_source_domain(),
            self._src.type,
        )

        try:
            html_content = self._prepare_html_content(data, self._get_source_domain())
            soup = _get_soup(html_content)

            post_article = self._find_post_article(soup)
            if not post_article:
                article_selector = f"{self._config.article_tag}.{self._config.article_cls}"
                raise ParseStructureError(
                    url=self._get_source_domain(),
                    expected_structure=f"Article with selector '{article_selector}'",
                    found_structure="None",
                )

            post = self._parse_post_article(post_article)
            logger.info(
                "Finished parse_one for source '%s' (domain=%s, type=%s)",
                self._src.name,
                self._get_source_domain(),
                self._src.type,
            )
            return post

        except (ParseError, ParseContentError, ParseStructureError):
            raise

        except Exception as exc:
            error_msg = (
                f"Failed to parse_one for source '{self._src.name}' "
                f"(domain={self._get_source_domain()}, type={self._src.type}): {exc}"
            )
            logger.error(error_msg, exc_info=True)
            raise ParseError(error_msg)

    @override
    def parse_many(self, data: bytes) -> list[PostDraft]:
        logger.info(
            "Starting parse_many for source '%s' (domain=%s, type=%s)",
            self._src.name,
            self._get_source_domain(),
            self._src.type,
        )

        try:
            html_content = self._prepare_html_content(data, self._get_source_domain())
            soup = _get_soup(html_content)

            post_cards = self._find_post_cards(soup)
            if not post_cards:
                card_selector = f"{self._config.card_tag}.{self._config.card_cls}"
                raise ParseStructureError(
                    url=self._get_source_domain(),
                    expected_structure=f"Post cards with selector '{card_selector}'",
                    found_structure="None",
                )

            posts: list[PostDraft] = []
            for idx, card in enumerate(post_cards):
                try:
                    logger.debug("Starting parse post card (%d/%d)", idx + 1, len(post_cards))

                    post = self._parse_post_card(card)
                    posts.append(post)

                    logger.debug(
                        "Successfully parsed post card (%d/%d)",
                        idx + 1,
                        len(post_cards),
                    )

                except (ParseError, ParseContentError, ParseStructureError) as exc:
                    logger.warning(
                        "Failed to parse post card (%d/%d): %s",
                        idx + 1,
                        len(post_cards),
                        exc,
                    )
                    continue

                except Exception as exc:
                    logger.warning(
                        "Unexpected error parsing post card (%d/%d): %s",
                        idx + 1,
                        len(post_cards),
                        exc,
                    )
                    continue

            logger.info(
                "Finished parse_many for source '%s' (domain=%s, type=%s)",
                self._src.name,
                self._get_source_domain(),
                self._src.type,
            )
            return posts

        except (ParseError, ParseContentError, ParseStructureError):
            raise

        except Exception as exc:
            error_msg = (
                f"Failed to parse_many for source '{self._src.name}' "
                f"(domain={self._get_source_domain()}, type={self._src.type}): {exc}"
            )
            logger.error(error_msg, exc_info=True)
            raise ParseError(error_msg)

    def _prepare_html_content(self, data: bytes, url: str = "unknown") -> str:
        encoding = self._config.encoding or "utf-8"
        logger.debug("Decoding HTML content with encoding: '%s'", encoding)

        try:
            if not data:
                raise ParseContentError(
                    url=url,
                    parser_type="HTMLParser",
                    reason="HTML content is empty",
                )

            html_content = data.decode(encoding=encoding, errors="replace")

            length = utils.pretty_print_size(len(html_content))
            logger.debug("Successfully decoded HTML content (length=%s)", length)

            if not html_content.strip():
                raise ParseContentError(
                    url=url,
                    parser_type="HTMLParser",
                    reason="HTML content is empty after decoding",
                )

            return html_content

        except ParseContentError:
            raise

        except Exception as exc:
            logger.error("Failed to decode HTML content with %s encoding: %s", encoding, exc)
            raise ParseContentError(
                url=url,
                parser_type="HTMLParser",
                reason=f"Error decoding HTML content with {encoding} encoding: {exc}",
            ) from exc

    def _get_source_domain(self) -> str:
        return utils.domain(self._src.url)

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
        try:
            return HTMLParserConfig(
                article_tag="div",
                article_cls="article_article-page",
                card_tag="div",
                card_cls="listing__card",
                datetime_fmt="%Y-%m-%d %H:%M",
            )
        except Exception as exc:
            raise CrawlerConfigurationError(
                issue=f"Error creating RT parser config: {exc}",
                component="rt_parser_config",
            ) from exc

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
            logger.error("Failed to find post cards in HTML: %s", exc)
            expected_structure = f"Post cards with selector " f"'{self._config.card_tag}.{self._config.card_cls}'"
            raise ParseStructureError(
                url=self._get_source_domain(),
                expected_structure=expected_structure,
                found_structure=f"Search error: {exc}",
            )

    @override
    def _parse_post_card(self, card: Tag) -> PostDraft:
        try:
            title, relative_url = self._extract_post_details_from_card(card)
            absolute_url = urljoin(self._src.url, relative_url)
            post_id_raw = relative_url.strip("/").split("/")[-1]
            post_id = utils.normalize_id(post_id_raw, self._src.code_name)
            draft = PostDraft(id=post_id, title=title, url=absolute_url)
            return draft

        except ParseError:
            raise

        except Exception as exc:
            logger.error("Error parsing post card: %s", exc)
            raise ParseContentError(
                url=self._get_source_domain(),
                parser_type="RT",
                reason=f"Error parsing post card: {exc}",
            ) from exc

    @override
    def _find_post_article(self, soup: BeautifulSoup) -> Tag:
        logger.debug("Searching for post article in HTML (class='%s')", self._config.article_cls)

        try:
            post_article = soup.find(self._config.article_tag, class_=self._config.article_cls)
            if post_article:
                logger.info("Found post article in HTML")
            return post_article

        except Exception as exc:
            logger.error("Failed to find post article in HTML: %s", exc)
            expected_structure = f"Post article with selector '{self._config.article_tag}.{self._config.article_cls}'"
            raise ParseStructureError(
                url=self._get_source_domain(),
                expected_structure=expected_structure,
                found_structure=f"Search error: {exc}",
            )

    @override
    def _parse_post_article(self, article: Tag) -> PostDraft:
        try:
            content = self._extract_content_from_article(article)
            pub_date = self._extract_pub_date_from_article(article)
            draft = PostDraft(content=content, pub_date=pub_date)
            return draft

        except ParseError:
            raise

        except Exception as exc:
            error_msg = f"Error parsing post article: {exc}"
            logger.error(error_msg)
            raise ParseContentError(
                url=self._get_source_domain(),
                parser_type="RT",
                reason=error_msg,
            )

    def _extract_post_details_from_card(self, card: Tag) -> tuple[str, str]:
        try:
            heading_div = _get_required_tag(card, "div", "card__heading", self._get_source_domain())
            title_link = _get_required_tag(heading_div, "a", "link", self._get_source_domain())

            title_text = title_link.get_text(strip=True)
            title = " ".join(title_text.split())
            if not title.strip():
                raise ParseContentError(
                    url=self._get_source_domain(),
                    parser_type="RT",
                    reason="Post title is empty",
                )
            logger.debug("Post title extracted (length=%d)", len(title))

            relative_url = _get_required_attribute(title_link, "href", "Missing 'href' in 'a.link'")
            if not relative_url.strip():
                raise ParseContentError(
                    url=self._get_source_domain(),
                    parser_type="RT",
                    reason="Post url is empty",
                )
            logger.debug("Post url extracted (length=%d)", len(relative_url))

            return title, relative_url

        except ParseError:
            raise

        except Exception as exc:
            raise ParseContentError(
                url=self._get_source_domain(),
                parser_type="RT",
                reason=f"Error extracting post details from card: {exc}",
            ) from exc

    def _extract_content_from_article(self, article: Tag) -> str:
        try:
            article_div = _get_required_tag(
                article,
                "div",
                "article__text_article-page",
                self._get_source_domain(),
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

        except ParseError:
            raise

        except Exception as exc:
            raise ParseContentError(
                url=self._get_source_domain(),
                parser_type="RT",
                reason=f"Error extracting post content from article: {exc}",
            ) from exc

    def _extract_pub_date_from_article(self, article: Tag) -> datetime:
        try:
            time_tag = _get_required_tag(article, "time", "date", self._get_source_domain())
            pub_date_str = _get_required_attribute(time_tag, "datetime", self._get_source_domain())

            try:
                pub_date = datetime.strptime(pub_date_str, self._config.datetime_fmt)
                logger.debug("Post pub_date extracted: %s", pub_date)
                return pub_date

            except ValueError as exc:
                logger.error(
                    "Error parsing post pub_date '%s' with format '%s': %s",
                    pub_date_str,
                    self._config.datetime_fmt,
                    exc,
                )
                raise ParseContentError(
                    url=self._get_source_domain(),
                    parser_type="RT",
                    reason=f"Error parsing post pub_date '{pub_date_str}' "
                    f"with format '{self._config.datetime_fmt}': {exc}",
                )

        except ParseError:
            raise

        except Exception as exc:
            logger.error("Error parsing post pub_date: %s", exc)
            return TIME_1970_01_01
