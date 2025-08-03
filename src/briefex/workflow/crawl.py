from __future__ import annotations

import logging
from typing import Any, override
from uuid import UUID

from briefex.crawler import Crawler
from briefex.crawler import Post as CrawlerPost
from briefex.crawler import Source as CrawlerSource
from briefex.storage import Post as StoragePost
from briefex.storage import PostStorage, SourceStorage
from briefex.storage import Source as StorageSource
from briefex.workflow.base import Workflow

_log = logging.getLogger(__name__)


class CrawlWorkflow(Workflow):
    """Execute crawling of sources and store new posts."""

    def __init__(
        self,
        *,
        crawl: Crawler,
        post_storage: PostStorage,
        source_storage: SourceStorage,
        lookback_days: int = 3,
        **kwargs: Any,
    ) -> None:
        kwargs.update(
            {
                "crawler": crawl,
                "post_storage": post_storage,
                "source_storage": source_storage,
                "recent_posts_days": lookback_days,
            }
        )
        super().__init__(*[], **kwargs)
        self._crawler = crawl
        self._post_storage = post_storage
        self._source_storage = source_storage
        self._lookback_days = lookback_days

    @override
    def run(self) -> None:
        """Run the crawl workflow: fetch, crawl, and persist posts."""
        _log.info("Starting crawl workflow")

        try:
            recent_post_urls = self._fetch_recent_post_urls()
            fresh_posts_by_source = self._crawl_all_sources(recent_post_urls)
            self._persist_posts(fresh_posts_by_source)
        except Exception:
            _log.exception("Crawl workflow failed unexpectedly")
            raise

        _log.info("Crawl workflow completed successfully")

    def _fetch_recent_post_urls(self) -> set[str]:
        """Retrieve URLs of recent posts from storage."""
        _log.info(
            "Fetching posts from storage for the past %d days",
            self._lookback_days,
        )

        try:
            posts = self._post_storage.get_recent(days=self._lookback_days)
            urls = {post.canonical_url for post in posts}
        except Exception as exc:
            _log.error("Error fetching recent posts from storage: %s", exc)
            raise

        _log.info("Fetched %d recent posts from storage", len(urls))
        return urls

    def _crawl_all_sources(
        self,
        recent_post_urls: set[str],
    ) -> dict[StorageSource, list[CrawlerPost]]:
        """Crawl all sources and filter out already stored posts."""
        try:
            sources = self._source_storage.get_all()
            _log.info("Starting crawl for %d sources", len(sources))

            new_posts: dict[StorageSource, list[CrawlerPost]] = {}
            for src in sources:
                crawler_source = self._to_crawler_source(src)
                raw_posts = self._crawler.crawl(crawler_source)

                cleaned_posts = self._remove_empty_or_duplicates(raw_posts)
                unseen_posts = self._exclude_already_stored(
                    cleaned_posts,
                    recent_post_urls,
                )

                if unseen_posts:
                    new_posts[src] = unseen_posts
                    _log.info("Source %s collected %d posts", src, len(unseen_posts))
                else:
                    _log.info("Source %s now new posts", src)

            return new_posts

        except Exception as exc:
            _log.error("Error during crawling sources: %s", exc)
            raise

    def _persist_posts(
        self,
        posts_by_source: dict[StorageSource, list[CrawlerPost]],
    ) -> None:
        """Persist new posts to storage by source."""
        total_new = sum(len(v) for v in posts_by_source.values())
        if total_new == 0:
            _log.info("No new posts to persist. Skipping...")
            return

        _log.info("Persisting %d new posts", total_new)
        for src, posts in posts_by_source.items():
            storage_posts = [self._to_storage_post(post, src.id) for post in posts]

            for idx, post in enumerate(storage_posts, start=1):
                _log.info("Persisting post [%d/%d]", idx, len(storage_posts))
                try:
                    self._post_storage.add(post)
                except Exception as exc:
                    _log.error("Error persisting post [%d/%d]: %s", exc)
                    continue

            _log.info("Persisted %d posts for source %s", len(posts), src)

    @staticmethod
    def _remove_empty_or_duplicates(posts: list[CrawlerPost]) -> list[CrawlerPost]:
        """Filter out posts with empty content or duplicate URLs."""
        seen: set[str] = set()
        result: list[CrawlerPost] = []

        for post in posts:
            if not post.content:
                _log.warning(
                    "Excluding post with empty content: %s",
                    post.canonical_url,
                )
                continue

            if post.canonical_url in seen:
                _log.warning("Excluding duplicate post URL: %s", post.canonical_url)
                continue

            seen.add(post.canonical_url)
            result.append(post)

        return result

    @staticmethod
    def _exclude_already_stored(
        posts: list[CrawlerPost],
        recent_post_urls: set[str],
    ) -> list[CrawlerPost]:
        """Exclude posts whose URLs are in the recent_post_urls set."""
        return [post for post in posts if post.canonical_url not in recent_post_urls]

    @staticmethod
    def _to_crawler_source(src: StorageSource) -> CrawlerSource:
        return CrawlerSource(
            name=src.name,
            code_name=src.code_name,
            type=src.type.value,
            url=src.url,
        )

    @staticmethod
    def _to_storage_post(post: CrawlerPost, src_id: UUID) -> StoragePost:
        return StoragePost(
            title=post.title,
            content=post.content,
            canonical_url=post.canonical_url,
            source_id=src_id,
        )
