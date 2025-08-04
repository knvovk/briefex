from __future__ import annotations

import logging
from contextlib import closing
from typing import TYPE_CHECKING, override

from briefex.crawler.base import Crawler
from briefex.crawler.exceptions import CrawlerError

if TYPE_CHECKING:
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
        _log.info("Starting crawl for source '%s'", src)

        try:
            with closing(self._fetcher_factory.create(src.type)) as fetcher:
                main_page = fetcher.fetch(src.url)
                parser = self._parser_factory.create(src)
                drafts = parser.parse_many(main_page)

                posts: list[Post] = []
                successful = 0
                failed = 0
                total = len(drafts)

                for idx, draft in enumerate(drafts, start=1):
                    _log.debug(
                        "Processing draft %d/%d for source '%s'",
                        idx,
                        total,
                        src,
                    )
                    try:
                        draft_page = fetcher.fetch(draft.canonical_url)
                        draft_data = parser.parse(draft_page)
                        draft.merge(draft_data)
                        posts.append(draft.to_post())

                        successful += 1
                        _log.debug(
                            "Draft %d/%d processed successfully",
                            idx,
                            total,
                        )
                    except Exception as exc:
                        failed += 1
                        _log.warning(
                            "Failed to process draft %d/%d for source '%s': %s",
                            idx,
                            total,
                            src,
                            exc,
                        )

                _log.info(
                    "Finished crawl for source '%s': "
                    "total=%d, successful=%d, failed=%d",
                    src,
                    total,
                    successful,
                    failed,
                )
                return posts

        except Exception as exc:
            _log.error("Crawl failed for source '%s': %s", src, exc)
            raise CrawlerError(
                message=f"Crawl failed for source '{src}': {exc}",
                details={"src_url": src.url},
            ) from exc
