import logging
from typing import override

import utils

from .base import BaseCrawler
from .exceptions import (
    CrawlerOperationError,
    FetchError,
    ParseError,
    PostProcessingError,
    create_fetch_error,
    create_parse_error,
)
from .fetchers import BaseFetcher
from .models import Post, PostDraft, Source

logger = logging.getLogger(__name__)


class Crawler(BaseCrawler):

    @override
    def crawl(self, src: Source) -> list[Post]:
        logger.info(
            "Starting crawl for source '%s' (domain=%s, type=%s)",
            src.name,
            utils.domain(src.url),
            src.type.name,
        )
        fetcher = None

        try:
            fetcher = self._get_fetcher(src)
            posts: list[Post] = []
            drafts = self._fetch_posts_from_main_page(fetcher, src)

            for idx, draft in enumerate(drafts):
                logger.info("Starting process draft (%d/%d)", idx + 1, len(drafts))

                try:
                    if draft.source is None:
                        draft.source = src

                    other = self._fetch_post_details_from_individual_page(fetcher, src, draft)
                    draft.merge(other)

                    post = PostDraft.to_post(draft)
                    posts.append(post)

                    logger.info("Successfully processed draft (%d/%d)", idx + 1, len(drafts))

                except (FetchError, ParseError) as exc:
                    logger.warning("Skipping draft due to error: %s", exc)
                    continue

                except Exception as exc:
                    logger.error("Unexpected error processing draft: %s", exc, exc_info=True)
                    continue

            logger.info(
                "Finished crawl for source %s (domain=%s, type=%s)",
                src.name,
                utils.domain(src.url),
                src.type.name,
            )
            return posts

        except Exception as exc:
            logger.error("Error crawling source %s: %s", src, exc, exc_info=exc)
            raise CrawlerOperationError(
                operation="crawl",
                source_name=src.name,
                error_details=str(exc),
            ) from exc

        finally:
            if fetcher:
                fetcher.close()

    def _fetch_posts_from_main_page(self, fetcher: BaseFetcher, src: Source) -> list[PostDraft]:
        try:
            response_data = fetcher.fetch(src.url)
            parser = self._get_parser(src)
            parsed_drafts = parser.parse_many(response_data)
            return parsed_drafts

        except Exception as exc:
            if "fetch" in str(type(exc)).lower():
                raise create_fetch_error(src.url, exc) from exc
            elif "parse" in str(type(exc)).lower():
                raise create_parse_error(src.url, src.type.name, exc) from exc
            else:
                raise CrawlerOperationError(
                    operation="fetch_posts_from_main_page",
                    source_name=src.name,
                    error_details=str(exc),
                ) from exc

    def _fetch_post_details_from_individual_page(
        self,
        fetcher: BaseFetcher,
        src: Source,
        draft: PostDraft,
    ) -> PostDraft:
        try:
            response_data = fetcher.fetch(draft.url)
            parser = self._get_parser(src)
            parsed_draft = parser.parse_one(response_data)
            return parsed_draft

        except Exception as exc:
            if "fetch" in str(type(exc)).lower():
                raise create_fetch_error(draft.url, exc) from exc
            elif "parse" in str(type(exc)).lower():
                raise create_parse_error(draft.url, src.type.name, exc) from exc
            else:
                raise PostProcessingError(
                    post_url=draft.url,
                    processing_stage="fetch_details",
                    error_details=str(exc),
                ) from exc
