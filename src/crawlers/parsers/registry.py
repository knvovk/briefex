import logging
from typing import Callable

from ..exceptions import CrawlerConfigurationError
from .base import Parser

logger = logging.getLogger(__name__)

ParserT = type[Parser]


class ParserRegistry(dict[str, ParserT]):

    def register(self, code_name: str, cls: ParserT) -> None:
        self._validate_parser_class(cls)
        self[code_name] = cls
        logger.debug("%s registered for %s", cls.__name__, code_name)

    def _validate_parser_class(self, cls: ParserT) -> None:
        if not isinstance(cls, type) or not issubclass(cls, Parser):
            raise CrawlerConfigurationError(
                issue=f"Class {cls.__name__} must be a subclass of Parser",
                component="parser_registration",
            )

    def get_parser_names(self) -> list[str]:
        return [cls.__name__ for cls in self.values()]


parser_registry = ParserRegistry()


def register(code_name: str) -> Callable[[ParserT], ParserT]:
    def decorator(cls: ParserT) -> ParserT:
        try:
            parser_registry.register(code_name, cls)
            return cls
        except CrawlerConfigurationError:
            raise
        except Exception as exc:
            logger.error(
                "Failed to register parser %s for %s: %s",
                cls.__name__,
                code_name,
                exc,
            )
            raise CrawlerConfigurationError(
                issue=f"Registration failed for {cls.__name__}: {exc}",
                component="parser_registration",
            ) from exc

    return decorator
