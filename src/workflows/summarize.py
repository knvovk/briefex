import logging
import uuid
from typing import override

import intelligence
import storage

from .base import Workflow

logger = logging.getLogger(__name__)


class SummarizeWorkflow(Workflow):

    @override
    def run(self) -> None:
        try:
            logger.info("SummarizeWorkflow started")
            posts = self._get_stored_posts()
            summarized_posts = self._summarize_posts(posts)
            self._update_stored_posts(summarized_posts)
            logger.info("SummarizeWorkflow completed")
        except Exception as exc:
            logger.error("SummarizeWorkflow failed", exc_info=exc)
            raise

    def _get_stored_posts(self) -> list[storage.Post]:
        logger.info("[1/3] Retrieving stored posts for summarization")
        try:
            posts = []
            for status in (
                storage.PostStatus.PENDING_SUMMARY,
                storage.PostStatus.SUMMARY_RETRY,
            ):
                posts.extend(self.c.post_storage.get_many(filters={"status": status}))
            logger.info("[1/3] Successfully retrieved %d posts", len(posts))
            return posts
        except Exception as exc:
            logger.error(
                "[1/3] Unexpected error during retrieving stored posts: %s",
                str(exc),
            )
            raise

    def _summarize_posts(
        self,
        posts: list[storage.Post],
    ) -> dict[uuid.UUID, dict[str, object]]:
        logger.info("[2/3] Starting summarization for %d posts", len(posts))
        results: dict[uuid.UUID, dict[str, object]] = {}

        for idx, post in enumerate(posts, 1):
            logger.info(
                "[2/3] Processing post (id=%s) (%d/%d)",
                post.id,
                idx,
                len(posts),
            )
            try:
                summary = self.c.summarizer.summarize(post.content)
                results[post.id] = {
                    "status": storage.PostStatus.SUMMARY_READY,
                    "summary": summary,
                }

            except intelligence.IntelligenceException as exc:
                logger.error(
                    "[2/3] %s during processing post (id=%s): %s",
                    exc.__class__.__name__,
                    post.id,
                    str(exc),
                )
                status = self._determine_status_from_exc(exc)
                results[post.id] = {"status": status}
                continue

            except Exception as exc:
                logger.error(
                    "[2/3] Unexpected error during processing post (id=%s): %s",
                    post.id,
                    str(exc),
                )
                results[post.id] = {"status": storage.PostStatus.SUMMARY_RETRY}
                continue

        logger.info("[2/3] Finished summarization for %d posts", len(results))
        return results

    def _update_stored_posts(self, results: dict[uuid.UUID, dict[str, object]]) -> None:
        logger.info("[3/3] Updating stored posts for summarization")
        for post_id, post_data in results.items():
            try:
                self.c.post_storage.update(post_id, post_data)
            except Exception as exc:
                logger.error(
                    "[3/3] Unexpected error during updating post (id=%s): %s",
                    post_id,
                    str(exc),
                )
                continue

        logger.info("[3/3] Finished updating stored posts for summarization")

    def _determine_status_from_exc(
        self,
        exc: intelligence.IntelligenceException,
    ) -> storage.PostStatus:
        reason = str(exc.details.get("reason", exc.message)).lower()
        if "filter" in reason or "censor" in reason:
            return storage.PostStatus.SUMMARY_CENSORED
        return storage.PostStatus.SUMMARY_RETRY
