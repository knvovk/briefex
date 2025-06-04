import logging
from typing import override

import utils
from .base import BaseCrawler
from .models import Source, Post, PostDraft

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
        try:
            posts: list[Post] = []
            drafts = self._fetch_posts_from_main_page(src)
            for idx, draft in enumerate(drafts):
                logger.info("Starting process draft (%d/%d)", idx + 1, len(drafts))
                try:
                    if draft.source is None:
                        draft.source = src
                    other = self._fetch_post_details_from_individual_page(src, draft)
                except Exception:
                    continue
                draft.merge(other)
                post = PostDraft.to_post(draft)
                posts.append(post)
                logger.info("Successfully processed draft (%d/%d)", idx + 1, len(drafts))
            logger.info(
                "Finished crawl for source %s (domain=%s, type=%s)",
                src.name,
                utils.domain(src.url),
                src.type.name,
            )
            return posts
        except Exception as exc:
            logger.error("Error crawling source %s: %s", src, str(exc), exc_info=exc)
            raise

    def _fetch_posts_from_main_page(self, src: Source) -> list[PostDraft]:
        fetcher = self._get_fetcher(src)
        response_data = fetcher.fetch(src.url)
        parser = self._get_parser(src)
        parsed_drafts = parser.parse_many(response_data)
        return parsed_drafts

    def _fetch_post_details_from_individual_page(self, src: Source, draft: PostDraft) -> PostDraft:
        fetcher = self._get_fetcher(src)
        response_data = fetcher.fetch(draft.url)
        parser = self._get_parser(src)
        parsed_draft = parser.parse_one(response_data)
        return parsed_draft
