import logging
from contextlib import contextmanager
from typing import Iterator, override

import utils

from .base import Crawler
from .exceptions import (
    CrawlerOperationError,
    FetchError,
    ParseError,
    PostProcessingError,
    create_fetch_error,
    create_parse_error,
)
from .fetchers import Fetcher
from .models import Post, PostDraft, Source

logger = logging.getLogger(__name__)


class CrawlContext:

    def __init__(self, source: Source):
        self.source = source
        self.total_drafts = 0
        self.processed_drafts = 0
        self.successful_posts = 0
        self.failed_drafts = 0


class DefaultCrawler(Crawler):

    @override
    def crawl(self, src: Source) -> list[Post]:
        context = CrawlContext(src)

        logger.info(
            "Starting crawl for source '%s' (domain=%s, type=%s)",
            src.name,
            utils.domain(src.url),
            src.type.name,
        )

        try:
            with self._get_managed_fetcher(src) as fetcher:
                drafts = self._fetch_posts_from_main_page(fetcher, src)
                context.total_drafts = len(drafts)

                posts = self._process_drafts(fetcher, src, drafts, context)

                self._log_crawl_summary(context)
                return posts

        except Exception as exc:
            logger.error("Error crawling source %s: %s", src.name, exc, exc_info=True)
            raise CrawlerOperationError(
                operation="crawl",
                source_name=src.name,
                error_details=str(exc),
            ) from exc

    @contextmanager
    def _get_managed_fetcher(self, src: Source) -> Iterator[Fetcher]:
        fetcher = None
        try:
            fetcher = self._get_fetcher(src)
            yield fetcher
        finally:
            if fetcher:
                fetcher.close()

    def _process_drafts(
        self,
        fetcher: Fetcher,
        src: Source,
        drafts: list[PostDraft],
        context: CrawlContext,
    ) -> list[Post]:
        posts: list[Post] = []

        for idx, draft in enumerate(drafts, 1):
            context.processed_drafts = idx

            logger.debug("Processing draft (%d/%d)", idx, context.total_drafts)

            try:
                post = self._process_single_draft(fetcher, src, draft)
                posts.append(post)
                context.successful_posts += 1

                logger.debug(
                    "Successfully processed draft (%d/%d)", idx, context.total_drafts
                )

            except (FetchError, ParseError) as exc:
                context.failed_drafts += 1
                logger.warning(
                    "Skipping draft (%d/%d) due to error: %s",
                    idx,
                    context.total_drafts,
                    exc,
                )

            except Exception as exc:
                context.failed_drafts += 1
                logger.error(
                    "Unexpected error processing draft (%d/%d): %s",
                    idx,
                    context.total_drafts,
                    exc,
                    exc_info=True,
                )

        return posts

    def _process_single_draft(
        self, fetcher: Fetcher, src: Source, draft: PostDraft
    ) -> Post:
        # Ensure draft has source reference
        if draft.source is None:
            draft.source = src

        # Fetch additional details and merge
        details = self._fetch_post_details_from_individual_page(fetcher, src, draft)
        draft.merge(details)

        return PostDraft.to_post(draft)

    def _fetch_posts_from_main_page(
        self, fetcher: Fetcher, src: Source
    ) -> list[PostDraft]:
        try:
            response_data = fetcher.fetch(src.url)
            parser = self._get_parser(src)
            return parser.parse_many(response_data)

        except Exception as exc:
            parsed_exc = self._parse_exception(exc, src.url, src.type.name)
            if parsed_exc:
                raise parsed_exc from exc

            raise CrawlerOperationError(
                operation="fetch_posts_from_main_page",
                source_name=src.name,
                error_details=str(exc),
            ) from exc

    def _fetch_post_details_from_individual_page(
        self,
        fetcher: Fetcher,
        src: Source,
        draft: PostDraft,
    ) -> PostDraft:
        try:
            response_data = fetcher.fetch(draft.url)
            parser = self._get_parser(src)
            return parser.parse_one(response_data)

        except Exception as exc:
            parsed_exc = self._parse_exception(exc, draft.url, src.type.name)
            if parsed_exc:
                raise parsed_exc from exc

            raise PostProcessingError(
                post_url=draft.url,
                processing_stage="fetch_details",
                error_details=str(exc),
            ) from exc

    def _parse_exception(  # noqa
        self,
        exc: Exception,
        url: str,
        source_type: str,
    ) -> Exception | None:
        exc_type_name = type(exc).__name__.lower()

        if "fetch" in exc_type_name:
            return create_fetch_error(url, exc)
        elif "parse" in exc_type_name:
            return create_parse_error(url, source_type, exc)

        return None

    def _log_crawl_summary(self, context: CrawlContext) -> None:  # noqa
        logger.info(
            "Finished crawl for source '%s' (domain=%s, type=%s) - "
            "Total: %d, Successful: %d, Failed: %d",
            context.source.name,
            utils.domain(context.source.url),
            context.source.type.name,
            context.total_drafts,
            context.successful_posts,
            context.failed_drafts,
        )
