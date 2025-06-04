import logging
from typing import override

import utils
from .base import BaseParserFactory, BaseParser
from ..models import Source

logger = logging.getLogger(__name__)

_registry: dict[str, type[BaseParser]] = {}


def register(code_name: str):
    def _decorator(cls: type[BaseParser]):
        _registry[code_name] = cls
        logger.debug(
            "%s (parser) registered with code_name: '%s'",
            cls.__name__,
            code_name,
        )
        return cls

    return _decorator


class ParserFactory(BaseParserFactory):

    def __init__(self) -> None:
        super().__init__()
        registered_parsers = self.get_supported_parsers()
        logger.info(
            "ParserFactory initialized with %d registered parsers: %s",
            len(registered_parsers),
            ", ".join(f"'{p}'" for p in registered_parsers),
        )

    @override
    def create(self, src: Source) -> BaseParser:
        logger.debug(
            "Creating parser for source '%s' (domain=%s, type=%s)",
            src.name,
            utils.domain(src.url),
            src.type.name,
        )
        try:
            parser_cls = _registry[src.code_name]
            logger.debug(
                "Found matching parser class: %s for code_name: '%s'",
                parser_cls.__name__,
                src.code_name,
            )
            parser = parser_cls(src)
            logger.info(
                "%s initialized for source '%s' (domain=%s, type=%s)",
                parser_cls.__name__,
                src.name,
                utils.domain(src.url),
                src.type.name,
            )
            return parser
        except KeyError:
            registered_parsers = self.get_supported_parsers()
            error_msg = f"Unsupported parser code_name: {src.code_name}"
            logger.error(
                "%s. Registered fetchers: %s",
                error_msg,
                ", ".join(f"'{p}'" for p in registered_parsers),
            )
            raise ValueError(error_msg) from None
        except Exception as exc:
            logger.exception(
                "Unexpected error creating parser for source '%s' (domain=%s, type=%s): %s",
                src.name,
                utils.domain(src.url),
                src.type.name,
                str(exc),
            )
            raise

    @staticmethod
    def get_supported_parsers() -> list[str]:
        return list(_registry.keys())
