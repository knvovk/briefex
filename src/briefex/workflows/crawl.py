import logging
from typing import override
from uuid import UUID

from briefex import crawlers, storage

from .base import Workflow

logger = logging.getLogger(__name__)


class CrawlWorkflow(Workflow):
    """Workflow for crawling content from sources and storing it.

    This workflow handles the entire process of crawling content from configured
    sources, filtering out already processed content, and storing new content
    in the database.
    """

    @override
    def run(self) -> None:
        """Execute the crawling workflow.

        This method orchestrates the entire crawling process:
        1. Retrieves already stored URLs to avoid duplicates
        2. Crawls all configured sources for new content
        3. Filters out already processed content
        4. Stores new content in the database

        Raises:
            Exception: If any step of the workflow fails
        """
        try:
            logger.info("Starting crawling workflow")
            stored_urls = self._get_stored_canonical_urls()
            crawled_posts = self._crawl_all()
            filtered_posts = self._filter_posts(crawled_posts, stored_urls)
            self._store_posts(filtered_posts)
            logger.info("Finished crawling workflow")
        except Exception as exc:
            logger.error("Crawl workflow failed", exc_info=exc)
            raise

    def _get_stored_canonical_urls(self) -> set[str]:
        """Retrieve canonical URLs of recently stored posts.

        Fetches posts from the configured time period and extracts their
        canonical URLs to avoid duplicate processing.

        Returns:
            A set of canonical URLs from recently stored posts.

        Raises:
            Exception: If retrieving posts from storage fails.
        """
        try:
            days = self.c.settings.crawler.recent_posts_days
            logger.info("[1/4] Retrieving recent posts from storage (days=%d)", days)
            posts = self.c.post_storage.get_recent(days=days)
            logger.info("[1/4] Successfully retrieved %d recent posts", len(posts))
            return {post.canonical_url for post in posts}
        except Exception as exc:
            logger.error(
                "Unexpected error during retrieving recent posts: %s",
                str(exc),
            )
            raise

    def _crawl_all(self) -> dict[storage.Source, list[crawlers.Post]]:
        """Crawl all configured sources for content.

        Retrieves all sources from storage, converts them to crawler-compatible
        format, and crawls each source for content. The crawled posts are
        pre-filtered to remove duplicates and invalid entries.

        Returns:
            A dictionary mapping sources to their crawled posts.

        Raises:
            Exception: If crawling any source fails.
        """
        try:
            crawled_posts = {}
            all_srcs = self.c.src_storage.get_many()
            logger.info("[2/4] Starting crawl for %d sources", len(all_srcs))

            for src in all_srcs:
                crawler_src = self._cvt_to_crawlers_src(src)
                posts = self.c.crawler.crawl(crawler_src)
                crawled_posts[src] = self._prefilter_posts(posts)

            logger.info(
                "[2/4] Finished crawl for %d sources: %d posts",
                len(all_srcs),
                len(sum(crawled_posts.values(), [])),
            )
            return crawled_posts

        except Exception as exc:
            logger.error("Unexpected error during crawling sources: %s", str(exc))
            raise

    def _prefilter_posts(self, posts: list[crawlers.Post]) -> list[crawlers.Post]:
        """Pre-filter crawled posts to remove invalid or duplicate entries.

        Filters out posts with empty content and removes duplicates based on URL.
        This is an initial filtering step performed during the crawling phase.

        Args:
            posts: List of posts crawled from a source.

        Returns:
            Filtered list of posts with duplicates and invalid entries removed.
        """
        logger.debug("[2/4] Pre-filtering %d posts", len(posts))
        seen_urls = set()
        included_posts = []

        for post in posts:
            if len(post.content) == 0:
                logger.warning("[2/4] Skipping post with empty content: %s", post.url)
                continue

            if post.url not in seen_urls:
                seen_urls.add(post.url)
                included_posts.append(post)
            else:
                logger.warning("[2/4] Skipping post with duplicated URL: %s", post.url)

        if len(posts) != len(included_posts):
            logger.debug(
                "[2/4] Successfully pre-filtered posts "
                "(total=%d, included=%d, excluded=%d)",
                len(posts),
                len(included_posts),
                len(posts) - len(included_posts),
            )
        return included_posts

    def _filter_posts(
        self,
        crawled_posts: dict[storage.Source, list[crawlers.Post]],
        stored_urls: set[str],
    ) -> dict[storage.Source, list[crawlers.Post]]:
        """Filter crawled posts against already stored posts.

        Compares the URLs of crawled posts with the URLs of posts already in storage
        to avoid storing duplicates. Sources with no new posts are removed from
        the result.

        Args:
            crawled_posts: Dictionary mapping sources to their crawled posts.
            stored_urls: Set of URLs for posts already in storage.

        Returns:
            Dictionary mapping sources to their filtered posts (only new posts).

        Raises:
            Exception: If filtering posts fails.
        """
        try:
            filtered_posts = {}
            for src, posts in crawled_posts.items():
                logger.info(
                    "[3/4] Filtering %d posts for source %s [stored_urls=%s]",
                    len(posts),
                    src,
                    len(stored_urls),
                )

                included_posts = []
                for post in posts:
                    if post.url not in stored_urls:
                        included_posts.append(post)
                    else:
                        logger.warning(
                            "[3/4] Skipping post with duplicated URL: %s",
                            post.url,
                        )

                if not included_posts:
                    logger.info("[3/4] No new posts found for source %s", src)
                    continue

                filtered_posts[src] = included_posts
                logger.info(
                    "[3/4] Successfully filtered posts "
                    "(total=%d, included=%d, excluded=%d)",
                    len(posts),
                    len(included_posts),
                    len(posts) - len(included_posts),
                )

            return filtered_posts

        except Exception as exc:
            logger.error("Unexpected error during filtering posts: %s", str(exc))
            raise

    def _store_posts(
        self,
        crawled_posts: dict[storage.Source, list[crawlers.Post]],
    ) -> None:
        """Store filtered posts in the database.

        Converts crawler post objects to storage post objects and stores them
        in the database. Skip sources with no posts to store.

        Args:
            crawled_posts: Dictionary mapping sources to their filtered posts.

        Raises:
            Exception: If storing posts fails.
        """
        total = sum(map(len, crawled_posts.values()))
        if total == 0:
            return

        logger.info("[4/4] Storing crawled posts (total=%d)", total)
        try:
            for src, posts in crawled_posts.items():
                if not posts:
                    logger.debug(
                        "[4/4] No new posts to store for source %s",
                        src,
                    )
                    continue

                posts_to_store = []
                for post in posts:
                    converted_post = self._cvt_to_storage_post(post, src.id)
                    posts_to_store.append(converted_post)

                self.c.post_storage.add_many(posts_to_store)
                logger.info(
                    "[4/4] Successfully stored %d posts for source %s",
                    len(posts),
                    src,
                )

        except Exception as exc:
            logger.error("Unexpected error during storing posts: %s", str(exc))
            raise

    @staticmethod
    def _cvt_to_crawlers_src(obj: storage.Source) -> crawlers.Source:
        """Convert a storage Source object to a crawler Source object.

        Args:
            obj: Storage Source object to convert.

        Returns:
            Crawler Source object with equivalent data.
        """
        return crawlers.Source(
            name=obj.name,
            code_name=obj.code_name,
            type=crawlers.SourceType(obj.type.value),
            url=obj.url,
        )

    @staticmethod
    def _cvt_to_storage_post(obj: crawlers.Post, src_id: UUID) -> storage.Post:
        """Convert a crawler Post object to a storage Post object.

        Args:
            obj: Crawler Post object to convert.
            src_id: UUID of the source this post belongs to.

        Returns:
            Storage Post object with data from the crawler Post.
        """
        return storage.Post(
            title=obj.title,
            content=obj.content,
            canonical_url=obj.url,
            source_id=src_id,
        )
