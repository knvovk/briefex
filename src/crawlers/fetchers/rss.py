import logging
from typing import override

from ..exceptions import FetchError
from ..models import SourceType
from .base import BaseFetcher
from .factory import register

logger = logging.getLogger(__name__)


@register(SourceType.RSS)
class RSSFetcher(BaseFetcher):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        logger.debug("RSSFetcher initialized (not implemented)")

    @override
    def fetch(self, url: str) -> bytes:
        logger.info("RSS fetch requested for: %s", url)

        error_message = (
            f"RSS fetching is not yet implemented for URL: {url}. "
            "This fetcher requires RSS parsing logic to be added."
        )

        logger.error("RSS fetch failed: %s", error_message)
        raise FetchError(error_message)

    @override
    def close(self) -> None:
        logger.debug("RSSFetcher close called - no resources to clean up")
