import logging
from typing import override

import utils
from .base import BaseParser
from ..models import PostDraft

logger = logging.getLogger(__name__)


class RSSParser(BaseParser):
    _datetime_fmt: str = "%a, %d %b %Y %H:%M:%S %z"

    @override
    def parse_one(self, data: bytes) -> PostDraft:
        logger.warning(
            "Parse_one called on RSSParser for %s (%s), which is not supported",
            self._src.name,
            utils.domain(self._src.url),
        )
        error_msg = (
            "RSSParser does not support parsing single items directly from raw feed data. "
            "Use parse_many() instead, or extract the specific item after parsing the entire feed."
        )
        logger.error("Unsupported operation: %s", error_msg)
        raise NotImplementedError(error_msg)

    @override
    def parse_many(self, data: bytes) -> list[PostDraft]:
        logger.warning(
            "Parse_many called on RSSParser for %s (%s), which is not implemented",
            self._src.name,
            utils.domain(self._src.url),
        )
        error_msg = (
            "RSS feed parsing logic needs to be implemented in RSSParser.parse_many. "
            "Create a subclass of RSSParser and override this method with proper implementation."
        )
        logger.error("Implementation required: %s", error_msg)
        raise NotImplementedError(error_msg)
