import logging
from typing import Callable, override

import utils

from ..exceptions import CrawlerConfigurationError, InvalidSourceError, SourceNotFoundError
from ..models import Source
from .base import BaseParser, BaseParserFactory

logger = logging.getLogger(__name__)

_registry: dict[str, type[BaseParser]] = {}


def register(code_name: str) -> Callable[[type[BaseParser]], type[BaseParser]]:

    def _decorator(cls: type[BaseParser]) -> type[BaseParser]:
        try:
            if not issubclass(cls, BaseParser):
                raise CrawlerConfigurationError(
                    issue=f"Class {cls.__name__} is not a subclass of BaseParser",
                    component="parser_registration",
                )

            if code_name in _registry:
                logger.warning(
                    "Parser with code_name '%s' already registered. Overriding %s with %s",
                    code_name,
                    _registry[code_name].__name__,
                    cls.__name__,
                )

            _registry[code_name] = cls
            logger.debug(
                "%s (parser) registered with code_name: '%s'",
                cls.__name__,
                code_name,
            )
            return cls
        except Exception as exc:
            logger.error("Error registering parser %s with code_name '%s': %s", cls.__name__, code_name, exc)
            raise CrawlerConfigurationError(
                issue=f"Error registering parser {cls.__name__} with code_name '{code_name}': {exc}",
                component="parser_registration",
            ) from exc

    return _decorator


class ParserFactory(BaseParserFactory):

    def __init__(self) -> None:
        try:
            registered_parsers = self.get_registered_parser_types()
            logger.info(
                "ParserFactory initialized with %d registered parsers: %s",
                len(registered_parsers),
                ", ".join(f"'{p}'" for p in registered_parsers),
            )
        except Exception as exc:
            logger.error("Error initializing ParserFactory: %s", exc)
            raise CrawlerConfigurationError(
                issue=f"Error initializing ParserFactory: {exc}",
                component="parser_factory_initialization",
            ) from exc

    @override
    def create(self, src: Source) -> BaseParser:
        logger.debug(
            "Creating parser for source '%s' (domain=%s, type=%s)",
            src.name,
            utils.domain(src.url),
            src.type.name,
        )

        try:
            self._validate_source(src)
        except Exception as exc:
            if isinstance(exc, (InvalidSourceError, SourceNotFoundError)):
                raise
            else:
                raise InvalidSourceError(
                    source_url=src.url,
                    reason=f"Error validating source: {exc}",
                ) from exc

        try:
            if not hasattr(src, "code_name") or not src.code_name:
                raise InvalidSourceError(
                    source_url=src.url,
                    reason="Source code_name is not specified",
                )

            if src.code_name not in _registry:
                registered_parsers = self.get_registered_parser_types()
                parsers_str = ", ".join(f"'{p}'" for p in registered_parsers)
                raise CrawlerConfigurationError(
                    issue=f"No parser registered for code_name: {src.code_name}. Registered parsers: {parsers_str}",
                    component="parser_selection",
                )

            parser_cls = self.get_parser_class(src.code_name)
            logger.debug(
                "Found matching parser class: %s for code_name: '%s'",
                parser_cls.__name__,
                src.code_name,
            )

            try:
                parser = parser_cls(src)
                logger.info(
                    "%s initialized for source '%s' (domain=%s, type=%s)",
                    parser_cls.__name__,
                    src.name,
                    utils.domain(src.url),
                    src.type.name,
                )
                return parser

            except Exception as exc:
                logger.error(
                    "Error instantiating parser %s for source '%s' (domain=%s, type=%s): %s",
                    parser_cls.__name__,
                    src.name,
                    utils.domain(src.url),
                    src.type.name,
                    exc,
                )
                raise CrawlerConfigurationError(
                    issue=f"Error instantiating parser {parser_cls.__name__} for source '{src.name}': {exc}",
                    component="parser_instantiation",
                ) from exc

        except (CrawlerConfigurationError, InvalidSourceError):
            raise

        except Exception as exc:
            logger.exception(
                "Unexpected error creating parser for source '%s' (domain=%s, type=%s): %s",
                src.name,
                utils.domain(src.url),
                src.type.name,
                exc,
            )
            raise CrawlerConfigurationError(
                issue=f"Unexpected error creating parser for source '{src.name}': {exc}",
                component="parser_creation",
            ) from exc

    @staticmethod
    def get_registered_parser_types() -> list[str]:
        return list(_registry.keys())

    @staticmethod
    def is_supported(code_name: str) -> bool:
        return code_name in _registry

    @staticmethod
    def get_parser_class(code_name: str) -> type[BaseParser] | None:
        try:
            return _registry.get(code_name)
        except Exception as exc:
            logger.error("Error getting parser class for code_name '%s': %s", code_name, exc)
            return None

    @staticmethod
    def _validate_source(src: Source) -> None:
        if not src:
            raise InvalidSourceError(
                source_url="unknown",
                reason="Source is not specified",
            )

        if not src.name or not src.name.strip():
            raise InvalidSourceError(
                source_url=src.url or "unknown",
                reason="Source name is not specified",
            )

        if not src.url or not src.url.strip():
            raise InvalidSourceError(
                source_url="",
                reason="Source URL is not specified",
            )

        if not src.type:
            raise InvalidSourceError(
                source_url=src.url,
                reason="Source type is not specified",
            )

        try:
            domain = utils.domain(src.url)
            if not domain:
                raise InvalidSourceError(
                    source_url=src.url,
                    reason="Source URL is not valid",
                )
        except Exception as exc:
            raise InvalidSourceError(
                source_url=src.url,
                reason=f"Error validating source URL: {exc}",
            )
