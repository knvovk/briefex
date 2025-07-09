import logging
from contextlib import contextmanager
from typing import Iterator, override

from .base import Crawler
from .exceptions import (
    CrawlerOperationError,
    FetchError,
    ParseError,
    create_fetch_error,
    create_parse_error,
)
from .fetchers import Fetcher
from .models import Post, PostDraft, Source

logger = logging.getLogger(__name__)


class CrawlContext:
    """Context for tracking crawl progress and statistics.

    This class maintains state during a crawl operation, including
    the source being crawled and various counters for tracking progress.

    Attributes:
        source: The source being crawled.
        total_drafts: Total number of post-drafts found.
        processed_drafts: Number of post-drafts processed so far.
        successful_posts: Number of posts successfully processed.
        failed_drafts: Number of post-drafts that failed processing.
    """

    def __init__(self, source: Source):
        """Initialize a new CrawlContext.

        Args:
            source: The source being crawled.
        """
        self.source = source
        self.total_drafts = 0
        self.processed_drafts = 0
        self.successful_posts = 0
        self.failed_drafts = 0


class CrawlerImpl(Crawler):
    """Implementation of the Crawler abstract class.

    This class provides a concrete implementation of the Crawler interface,
    handling the crawling of sources to extract posts.
    """

    @override
    def crawl(self, src: Source) -> list[Post]:
        """Crawl a source to extract posts.

        This method orchestrates the crawling process:
        1. Fetches post drafts from the main page
        2. Processes each draft to extract full post-details
        3. Logs a summary of the crawl

        Args:
            src: The source to crawl.

        Returns:
            A list of extracted posts.

        Raises:
            CrawlerOperationError: If an error occurs during crawling.
        """
        logger.info("Starting crawl for source %s", src)
        context = CrawlContext(src)

        try:
            with self._get_managed_fetcher(src) as fetcher:
                drafts = self._fetch_posts_from_main_page(fetcher, src)
                context.total_drafts = len(drafts)

                posts = self._process_drafts(fetcher, src, drafts, context)

                self._log_crawl_summary(context)
                return posts

        except Exception as exc:
            logger.error("Unexpected error during crawl: %s", exc)
            raise CrawlerOperationError(
                operation="crawl",
                src_name=src.name,
                reason=str(exc),
            ) from exc

    @contextmanager
    def _get_managed_fetcher(self, src: Source) -> Iterator[Fetcher]:
        """Get a managed fetcher for a source.

        This context manager ensures that the fetcher is properly closed
        when it is no longer necessary, even if an exception occurs.

        Args:
            src: The source to get a fetcher for.

        Yields:
            A fetcher for the source.

        Raises:
            CrawlerConfigurationError: If a fetcher cannot be created for the source.
        """
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
        """Process a list of post-drafts.

        For each draft, attempts to process it into a full post.
        Updates the context with progress information.

        Args:
            fetcher: The fetcher to use for additional requests.
            src: The source being crawled.
            drafts: The list of post-drafts to process.
            context: The crawl context to update.

        Returns:
            A list of successfully processed posts.
        """
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
                    "Unexpected error during processing draft (%d/%d): %s",
                    idx,
                    context.total_drafts,
                    exc,
                )

        return posts

    def _process_single_draft(
        self, fetcher: Fetcher, src: Source, draft: PostDraft
    ) -> Post:
        """Process a single post-draft into a full post.

        This method:
        1. Ensures the draft has source reference
        2. Fetches additional details from the individual post-page
        3. Merges the details with the draft
        4. Converts the draft to a full post

        Args:
            fetcher: The fetcher to use for additional requests.
            src: The source being crawled.
            draft: The post draft to process.

        Returns:
            A fully processed post.

        Raises:
            FetchError: If there's an error, fetch additional details.
            ParseError: If there's an error parsing the fetched content.
            ValueError: If the draft is missing required fields after processing.
        """
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
        """Fetch post drafts from the main page of a source.

        This method:
        1. Fetches the content from the source's main URL
        2. Parses the content to extract post-drafts

        Args:
            fetcher: The fetcher to use for the request.
            src: The source to fetch posts from.

        Returns:
            A list of post-drafts extracted from the main page.

        Raises:
            FetchError: If there's an error fetching the content.
            ParseError: If there's an error parsing the content.
            CrawlerOperationError: For other unexpected errors.
        """
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
                src_name=src.name,
                reason=str(exc),
            ) from exc

    def _fetch_post_details_from_individual_page(
        self,
        fetcher: Fetcher,
        src: Source,
        draft: PostDraft,
    ) -> PostDraft:
        """Fetch additional details for a post from its individual page.

        This method:
        1. Fetches the content from the post's individual URL
        2. Parses the content to extract additional post-details

        Args:
            fetcher: The fetcher to use for the request.
            src: The source the post belongs to.
            draft: The post draft containing the URL to fetch.

        Returns:
            A post draft with additional details from the individual page.

        Raises:
            FetchError: If there's an error fetching the content.
            ParseError: If there's an error parsing the content.
            PostProcessingError: For other unexpected errors.
        """
        try:
            response_data = fetcher.fetch(draft.url)
            parser = self._get_parser(src)
            return parser.parse_one(response_data)

        except Exception as exc:
            parsed_exc = self._parse_exception(exc, draft.url, src.type.name)
            if parsed_exc:
                raise parsed_exc from exc

            raise CrawlerOperationError(
                operation="fetch_post_details_from_individual_page",
                src_name=src.name,
                reason=str(exc),
            ) from exc

    def _parse_exception(
        self,
        exc: Exception,
        url: str,
        src_type: str,
    ) -> Exception | None:
        """Parse an exception to determine its type and create a more specific exception.

        This method examines the exception type name to determine if it's a fetch
        or parse error and creates a more specific exception with additional context.

        Args:
            exc: The exception to parse.
            url: The URL that was being processed when the exception occurred.
            src_type: The type of the source being processed.

        Returns:
            A more specific exception if the exception type is recognized, None otherwise.
        """
        exc_type_name = type(exc).__name__.lower()

        if "fetch" in exc_type_name:
            return create_fetch_error(url, exc)
        elif "parse" in exc_type_name:
            return create_parse_error(url, src_type, exc)

        return None

    def _log_crawl_summary(self, ctx: CrawlContext) -> None:
        """Log a summary of the crawl results.

        This method logs information about the crawl results, including
        the total number of drafts found, the number of successful posts,
        and the number of failed drafts.

        Args:
            ctx: The crawl context containing the statistics to log.
        """
        logger.info(
            "Finished crawl for source %s [total=%d, successful=%d, failed=%d]",
            ctx.source,
            ctx.total_drafts,
            ctx.successful_posts,
            ctx.failed_drafts,
        )
