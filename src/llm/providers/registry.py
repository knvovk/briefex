import logging
from typing import Callable, Sequence

from ..exceptions import LLMConfigurationError
from ..models import Model
from .base import LLMProvider

logger = logging.getLogger(__name__)


class LLMProviderRegistry(dict[type[LLMProvider], Sequence[Model]]):

    def register(self, cls: type[LLMProvider], models: Sequence[Model]) -> None:
        self._validate_provider_class(cls)
        self[cls] = models
        logger.debug("%s registered for %s", cls.__name__, ", ".join(models))

    def _validate_provider_class(self, cls: type[LLMProvider]) -> None:
        if not isinstance(cls, type) or not issubclass(cls, LLMProvider):
            raise LLMConfigurationError(
                issue=f"Class {cls.__name__} must be a subclass of LLMProvider",
                component="provider_registration",
            )

    def get_provider_names(self) -> list[str]:
        return [cls.__name__ for cls in self.keys()]


llm_provider_registry = LLMProviderRegistry()


def register(
    models: Sequence[Model],
) -> Callable[[type[LLMProvider]], type[LLMProvider]]:
    def decorator(cls: type[LLMProvider]) -> type[LLMProvider]:
        try:
            llm_provider_registry.register(cls, models)
            return cls
        except LLMConfigurationError:
            raise
        except Exception as exc:
            logger.error(
                "Failed to register LLM provider %s for %s: %s",
                cls.__name__,
                ", ".join(models),
                exc,
            )
            raise LLMConfigurationError(
                issue=f"Registration failed for {cls.__name__}: {exc}",
                component="provider_registration",
            )

    return decorator
