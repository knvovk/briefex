from __future__ import annotations

import logging
from typing import Any, override

from briefex.crawler.fetchers.base import Fetcher
from briefex.crawler.fetchers.registry import register

_log = logging.getLogger(__name__)


@register("RSS")
class RSSFetcher(Fetcher):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        _log.debug("%s initialized (not implemented)", self.__class__.__name__)

    @override
    def fetch(self, url: str, **kwargs: Any) -> bytes:
        _log.warning("%s not implemented", self.__class__.__name__)
        return b""

    @override
    def close(self) -> None:
        _log.warning("%s not implemented", self.__class__.__name__)
