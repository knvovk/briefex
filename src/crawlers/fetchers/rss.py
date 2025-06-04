import logging
from typing import override

from .base import BaseFetcher
from .factory import register
from ..models import SourceType

logger = logging.getLogger(__name__)


@register(SourceType.RSS)
class RSSFetcher(BaseFetcher):

    @override
    def fetch(self, url: str) -> bytes:
        logger.warning("Fetch called on RSSFetcher for %s, which is not implemented", url)
        error_msg = (
            "RSS fetching logic needs to be implemented in RSSFetcher.fetch. "
            "Create a subclass of RSSFetcher and override this method with proper implementation."
        )
        logger.error("Implementation required: %s", error_msg)
        raise NotImplementedError(error_msg)
