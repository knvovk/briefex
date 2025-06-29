import logging
from abc import ABC, abstractmethod
from typing import Callable, override

from ..exceptions import CrawlerConfigurationError
from ..models import Source
from .base import Parser

logger = logging.getLogger(__name__)

ParserT = type[Parser]


class ParserRegistry:

    def __init__(self) -> None:
        self._registry: dict[str, ParserT] = {}

    def register(self, code_name: str, parser_class: ParserT) -> None:
        self._validate_parser_class(parser_class)
        self._registry[code_name] = parser_class
        logger.debug("%s registered for %s", parser_class.__name__, code_name)

    def get(self, code_name: str) -> ParserT | None:
        return self._registry.get(code_name)

    def is_registered(self, code_name: str) -> bool:
        return code_name in self._registry

    def get_registered_code_names(self) -> list[str]:
        return list(self._registry.keys())

    def _validate_parser_class(self, parser_class: ParserT) -> None:
        if not isinstance(parser_class, type) or not issubclass(parser_class, Parser):
            raise CrawlerConfigurationError(
                issue=f"Class {parser_class.__name__} must be a subclass of Parser",
                component="parser_registration",
            )


_parser_registry = ParserRegistry()


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
        parser_class = self._get_parser_class(src.code_name)
        return self._instantiate_parser(parser_class, src)

    def _get_parser_class(self, code_name: str) -> ParserT | None:
        parser_class = _parser_registry.get(code_name)

        if parser_class is None:
            code_names = _parser_registry.get_registered_code_names()
            parser_list = [_parser_registry.get(c).__name__ for c in code_names]
            raise CrawlerConfigurationError(
                issue=f"No parser registered for source with code_name {code_name}. "
                f"Registered parsers: {', '.join(parser_list or 'None')}",
                component="parser_selection",
            )

        return parser_class

    def _instantiate_parser(
        self,
        parser_class: ParserT,
        src: Source,
    ) -> Parser:
        try:
            parser = parser_class(src)
            logger.info("%s initialized for %s", parser_class.__name__, src)
            return parser

        except Exception as exc:
            logger.error("Failed to instantiate %s: %s", parser_class.__name__, exc)
            raise CrawlerConfigurationError(
                issue=f"Parser instantiation failed for {parser_class.__name__}: {exc}",
                component="parser_instantiation",
            ) from exc

    def _log_initialization(self) -> None:
        code_names = _parser_registry.get_registered_code_names()
        parser_list = [_parser_registry.get(p).__name__ for p in code_names]
        logger.info(
            "ParserFactory initialized with %d registered parsers: %s",
            len(code_names),
            ", ".join(parser_list),
        )


def register(code_name: str) -> Callable[[ParserT], ParserT]:
    def decorator(parser_class: ParserT) -> ParserT:
        try:
            _parser_registry.register(code_name, parser_class)
            return parser_class
        except Exception as exc:
            logger.error(
                "Failed to register parser %s for %s: %s",
                parser_class.__name__,
                code_name,
                exc,
            )
            raise CrawlerConfigurationError(
                issue=f"Registration failed for {parser_class.__name__}: {exc}",
                component="parser_registration",
            ) from exc

    return decorator


def create_default_parser_factory() -> ParserFactory:
    return DefaultParserFactory()
