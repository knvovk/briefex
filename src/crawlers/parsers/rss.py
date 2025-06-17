import logging
from typing import override

from ..exceptions import ParseError
from ..models import PostDraft
from .base import BaseParser

logger = logging.getLogger(__name__)


class RSSParser(BaseParser):
    _datetime_fmt: str = "%a, %d %b %Y %H:%M:%S %z"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        logger.debug("RSSParser initialized (not implemented)")

    @override
    def parse_one(self, data: bytes) -> PostDraft:
        logger.info("Parsing single article for %s", self._src.name)

        error_message = (
            f"RSS parsing is not yet implemented for source {self._src.name}. "
            "This parser requires RSS parsing logic to be added."
        )

        logger.error("RSS parsing failed: %s", error_message)
        raise ParseError(error_message)

    @override
    def parse_many(self, data: bytes) -> list[PostDraft]:
        logger.info("Parsing multiple articles for %s", self._src.name)

        error_message = (
            f"RSS parsing is not yet implemented for source {self._src.name}. "
            "This parser requires RSS parsing logic to be added."
        )

        logger.error("RSS parsing failed: %s", error_message)
        raise ParseError(error_message)
