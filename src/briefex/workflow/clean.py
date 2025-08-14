from __future__ import annotations

import logging
from typing import Any, override

from briefex.storage import Post, PostStatus, PostStorage
from briefex.workflow.base import Workflow

_log = logging.getLogger(__name__)


class CleanWorkflow(Workflow):
    """Workflow that deletes posts marked as censored."""

    def __init__(
        self,
        *,
        post_storage: PostStorage,
        **kwargs: Any,
    ) -> None:
        kwargs.update(
            {
                "post_storage": post_storage,
            }
        )
        super().__init__(*[], **kwargs)
        self._post_storage = post_storage

    @override
    def run(self) -> None:
        """Execute the cleanup: collect censored posts and delete them."""
        _log.info("Starting clean workflow")

        try:
            censored_posts = self._collect_censored_posts()
            self._delete_posts(censored_posts)
        except Exception:
            _log.exception("Clean workflow failed unexpectedly")
            raise

        _log.info("Clean workflow completed successfully")

    def _collect_censored_posts(self) -> list[Post]:
        """Fetch posts currently marked as censored in storage."""
        _log.info("Fetching censored posts from storage for cleaning")
        posts: list[Post] = []

        try:
            status = PostStatus.SUMMARY_CENSORED
            batch = self._post_storage.get_all(filters={"status": status})
            _log.debug("Fetched %d posts with status %r", len(batch), status)
            posts.extend(batch)

        except Exception as exc:
            _log.error("Error fetching censored posts from storage: %s", exc)
            raise

        _log.info("Fetched %d censored posts from storage", len(posts))
        return posts

    def _delete_posts(self, posts: list[Post]) -> None:
        """Delete provided posts from storage; skip gracefully if empty."""
        if not posts:
            _log.info("No posts to delete. Skipping...")
            return

        _log.info("Deleting %d posts", len(posts))
        for post in posts:
            try:
                self._post_storage.delete(post.id)
            except Exception as exc:
                _log.error("Error deleting post (id=%s): %s", post.id, exc)
                continue
