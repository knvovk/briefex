from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, override

from briefex.intelligence import IntelligenceError
from briefex.storage import Post, PostStatus, PostStorage
from briefex.workflow.base import Workflow

if TYPE_CHECKING:
    from collections.abc import Mapping
    from uuid import UUID

    from briefex.intelligence.summarization import Summarizer

_log = logging.getLogger(__name__)


class SummarizeWorkflow(Workflow):
    """Execute summarization of pending posts and persist updates."""

    def __init__(
        self,
        *,
        post_storage: PostStorage,
        summarizer: Summarizer,
        **kwargs: Any,
    ) -> None:
        kwargs.update(
            {
                "post_storage": post_storage,
                "summarizer": summarizer,
            }
        )
        super().__init__(*[], **kwargs)
        self._post_storage = post_storage
        self._summarizer = summarizer

    @override
    def run(self) -> None:
        """Run the summarization workflow end to end."""
        _log.info("Starting summarization workflow")

        try:
            pending_posts = self._collect_pending_posts()
            update_map = self._summarize_batch(pending_posts)
            self._persist_updates(update_map)
        except Exception:
            _log.exception("Summarization workflow failed unexpectedly")
            raise

        _log.info("Summarization workflow completed successfully")

    def _collect_pending_posts(self) -> list[Post]:
        """Fetch posts with pending or retry status from storage."""
        _log.info("Fetching pending posts from storage for summarization")
        pending_statuses = [PostStatus.PENDING_SUMMARY, PostStatus.SUMMARY_RETRY]
        posts: list[Post] = []

        for status in pending_statuses:
            try:
                batch = self._post_storage.get_all(filters={"status": status})
                _log.debug("Fetched %d posts with status %r", len(batch), status)
                posts.extend(batch)

            except Exception as exc:
                _log.error("Error fetching pending posts from storage: %s", exc)
                continue

        _log.info("Fetched %d pending posts from storage", len(posts))
        return posts

    def _summarize_batch(self, posts: list[Post]) -> dict[UUID, Mapping[str, object]]:
        """Generate summaries for a batch of posts."""
        update_map: dict[UUID, Mapping[str, object]] = {}
        total = len(posts)

        for idx, post in enumerate(posts, 1):
            _log.info("Summarizing post %d/%d (id=%s)", idx, total, post.id)
            update_map[post.id] = self._summarize_single(post)

        _log.info("Summarization finished for %d posts", total)
        return update_map

    def _summarize_single(self, post: Post) -> Mapping[str, object]:
        """Summarize a single post and determine its next status."""
        try:
            summary_text = self._summarizer.summarize(post.content)
            _log.debug(
                "Post (id=%s) summarized (output length: %d chars)",
                post.id,
                len(summary_text),
            )
            return {"status": PostStatus.SUMMARY_READY, "summary": summary_text}

        except IntelligenceError as exc:
            _log.warning(
                "%s while summarizing post (id=%s): %s",
                exc.__class__.__name__,
                post.id,
                exc,
            )
            return {"status": self._status_for_exception(exc)}

        except Exception as exc:
            _log.error("Unexpected error for post (id=%s): %s", post.id, exc)
            return {"status": PostStatus.SUMMARY_RETRY}

    def _persist_updates(self, update_map: dict[UUID, Mapping[str, object]]) -> None:
        """Persist summary updates to storage."""
        if not update_map:
            _log.info("No updates to persist. Skipping...")
            return

        _log.info("Persisting updates for %d posts", len(update_map))
        for post_id, payload in update_map.items():
            try:
                self._post_storage.update(post_id, payload)
                _log.debug(
                    "Updated post (id=%s) to status %r",
                    post_id,
                    payload["status"],
                )
            except Exception as exc:  # pragma: no cover
                _log.error("Failed to update post (id=%s): %s", post_id, exc)
                continue

    @staticmethod
    def _status_for_exception(exc: IntelligenceError) -> PostStatus:
        reason = str(exc.details.get("reason", exc.message)).lower()
        if any(key in reason for key in ("filter", "censor")):
            return PostStatus.SUMMARY_CENSORED
        return PostStatus.SUMMARY_RETRY
