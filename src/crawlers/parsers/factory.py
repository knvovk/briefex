import logging
from abc import ABC, abstractmethod
from typing import Callable, override

from ..exceptions import CrawlerConfigurationError
from ..models import Source
from .base import BaseParser

logger = logging.getLogger(__name__)


class ParserRegistry:

    def __init__(self) -> None:
        self._registry: dict[str, type[BaseParser]] = {}

    def register(self, code_name: str, parser_class: type[BaseParser]) -> None:
        self._validate_parser_class(parser_class)
        self._registry[code_name] = parser_class
        logger.debug(
            "Registered %s for parser code_name %s",
            parser_class.__name__,
            code_name,
        )

    def get(self, code_name: str) -> type[BaseParser] | None:
        return self._registry.get(code_name)

    def is_registered(self, code_name: str) -> bool:
        return code_name in self._registry

    def get_registered_types(self) -> list[str]:
        return list(self._registry.keys())

    def _validate_parser_class(self, parser_class: type[BaseParser]) -> None:  # noqa
        if not isinstance(parser_class, type) or not issubclass(
            parser_class, BaseParser
        ):
            raise CrawlerConfigurationError(
                issue=f"Class {parser_class.__name__} must be a subclass of BaseParser",
                component="parser_registration",
            )


_parser_registry = ParserRegistry()


def register(code_name: str) -> Callable[[type[BaseParser]], type[BaseParser]]:
    def decorator(parser_class: type[BaseParser]) -> type[BaseParser]:
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


class BaseParserFactory(ABC):

    @abstractmethod
    def create(self, src: Source) -> BaseParser: ...


class ParserFactory(BaseParserFactory):

    def __init__(self) -> None:
        self._log_initialization()

    @override
    def create(self, src: Source) -> BaseParser:
        logger.debug("Creating parser for source: %s", src)

        parser_class = self.get_parser_class(src.code_name)
        return self._instantiate_parser(parser_class, src)

    def get_registered_parser_types(self) -> list[str]:  # noqa
        return _parser_registry.get_registered_types()

    def is_supported(self, code_name: str) -> bool:  # noqa
        return _parser_registry.is_registered(code_name)

    def get_parser_class(self, code_name: str) -> type[BaseParser] | None:  # noqa
        parser_class = _parser_registry.get(code_name)

        if parser_class is None:
            registered_types = [t for t in self.get_registered_parser_types()]
            raise CrawlerConfigurationError(
                issue=(
                    f"No parser registered for code_name '{code_name}'. "
                    f"Available types: {', '.join(registered_types) or 'none'}"
                ),
                component="parser_selection",
            )
        return parser_class

    def _instantiate_parser(  # noqa
        self,
        parser_class: type[BaseParser],
        src: Source,
    ) -> BaseParser:
        try:
            parser = parser_class(src)
            logger.info(
                "Successfully created %s for source %s",
                parser_class.__name__,
                src.name,
            )
            return parser
        except Exception as exc:
            logger.error("Failed to instantiate %s: %s", parser_class.__name__, exc)
            raise CrawlerConfigurationError(
                issue=f"Parser instantiation failed for {parser_class.__name__}: {exc}",
                component="parser_instantiation",
            ) from exc

    def _log_initialization(self) -> None:
        registered_types = self.get_registered_parser_types()
        logger.info(
            "ParserFactory initialized with %d registered parsers: %s",
            len(registered_types),
            ", ".join(registered_types),
        )
