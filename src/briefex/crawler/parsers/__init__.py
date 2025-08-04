from __future__ import annotations

import briefex.crawler.parsers.html
import briefex.crawler.parsers.rss  # noqa: F401
from briefex.crawler.parsers.base import Parser, ParserFactory
from briefex.crawler.parsers.factory import DefaultParserFactory

_parser_factory: ParserFactory | None = None


def get_default_parser_factory() -> ParserFactory:
    global _parser_factory

    if _parser_factory is None:
        _parser_factory = DefaultParserFactory()

    return _parser_factory


__all__ = ["Parser", "ParserFactory", "get_default_parser_factory"]
