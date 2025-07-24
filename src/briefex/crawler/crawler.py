from __future__ import annotations

import logging
from contextlib import closing
from typing import override

from briefex.crawler.base import Crawler
from briefex.crawler.exceptions import CrawlerException
from briefex.crawler.models import Post, Source

_log = logging.getLogger(__name__)


class DefaultCrawler(Crawler):
    """Crawler that fetches pages, parses drafts, and returns Posts."""

    @override
    def crawl(self, src: Source) -> list[Post]:
        """Crawl the given source and return parsed posts.

        Args:
            src: Source configuration for crawling.

        Returns:
            A list of successfully parsed Post objects.

        Raises:
            CrawlerException: If an unexpected error occurs during crawl.
        """
        _log.info("Starting crawl for source %s", src)

        try:
            with closing(self._fetcher_factory.create(src.type)) as fetcher:
                main_page = fetcher.fetch(src.url)
                parser = self._parser_factory.create(src)
                drafts = parser.parse_many(main_page)

                posts: list[Post] = []
                successful, failed = 0, 0
                for idx, draft in enumerate(drafts, start=1):
                    _log.debug("Processing draft (%d/%d)", idx, len(drafts))
                    try:
                        draft_page = fetcher.fetch(draft.canonical_url)
                        draft_data = parser.parse(draft_page)

                        draft.merge(draft_data)
                        posts.append(draft.to_post())

                        successful += 1
                        _log.debug(
                            "Successfully processed draft (%d/%d)",
                            idx,
                            len(drafts),
                        )
                    except Exception as exc:
                        failed += 1
                        _log.error(
                            "Failed to process draft (%d/%d): %s",
                            idx,
                            len(drafts),
                            exc,
                        )

                _log.info(
                    "Finished crawl for source %s (total=%s, successful=%s, failed=%s)",
                    src,
                    len(drafts),
                    successful,
                    failed,
                )
                return posts

        except Exception as exc:
            _log.error("Unexpected error during crawl: %s", exc)
            raise CrawlerException(
                message=f"Unexpected error during crawl: {exc}",
                details={
                    "src": src,
                },
            ) from exc
