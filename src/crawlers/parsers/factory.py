import logging
from abc import ABC, abstractmethod
from typing import override

from ..exceptions import CrawlerConfigurationError
from ..models import Source
from .base import Parser
from .registry import parser_registry

logger = logging.getLogger(__name__)

ParserT = type[Parser]


class ParserFactory(ABC):

    @abstractmethod
    def create(self, src: Source) -> Parser: ...


class DefaultParserFactory(ParserFactory):

    def __init__(self) -> None:
        super().__init__()
        self._log_initialization()

    @override
    def create(self, src: Source) -> Parser:
        logger.debug("Initializing parser for %s", src)
        cls = self._get_parser_class(src.code_name)
        return self._instantiate_parser(cls, src)

    @staticmethod
    def _get_parser_class(code_name: str) -> ParserT | None:
        if code_name not in parser_registry:
            available_parsers = parser_registry.get_parser_names()
            parsers_str = ", ".join(available_parsers) if available_parsers else "None"
            raise CrawlerConfigurationError(
                issue=f"No parser registered for source with code_name {code_name}. "
                f"Available parsers: {parsers_str}",
                component="parser_selection",
            )

        return parser_registry[code_name]

    @staticmethod
    def _instantiate_parser(cls: ParserT, src: Source) -> Parser:
        try:
            parser = cls(src)
            logger.info("%s initialized for %s", cls.__name__, src)
            return parser
        except Exception as exc:
            logger.error("Failed to instantiate %s: %s", cls.__name__, exc)
            raise CrawlerConfigurationError(
                issue=f"Parser instantiation failed for {cls.__name__}: {exc}",
                component="parser_instantiation",
            ) from exc

    @staticmethod
    def _log_initialization() -> None:
        parser_count = len(parser_registry)
        if parser_count == 0:
            logger.warning("ParserFactory initialized with no registered parsers")
            return

        parser_names = parser_registry.get_parser_names()
        logger.info(
            "ParserFactory initialized with %d parser%s: %s",
            parser_count,
            "s" if parser_count > 1 else "",
            ", ".join(parser_names),
        )


def create_default_parser_factory() -> ParserFactory:
    return DefaultParserFactory()
