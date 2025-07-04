import logging
from typing import Callable, Sequence

from .base import LLMClient
from .exceptions import LLMConfigurationError
from .models import Model

logger = logging.getLogger(__name__)

ClientT = type[LLMClient]


class LLMRegistry(dict[ClientT, Sequence[Model]]):

    def register(self, cls: ClientT, models: Sequence[Model]) -> None:
        self._validate_client_class(cls)
        self[cls] = models
        logger.debug("%s registered for %s", cls.__name__, ", ".join(models))

    def _validate_client_class(self, cls: ClientT) -> None:
        if not isinstance(cls, type) or not issubclass(cls, LLMClient):
            raise LLMConfigurationError(
                issue=f"Class {cls.__name__} must be a subclass of LLMClient",
                component="client_registration",
            )

    def get_client_names(self) -> list[str]:
        return [cls.__name__ for cls in self.keys()]


llm_registry = LLMRegistry()


def register(models: Sequence[Model]) -> Callable[[ClientT], ClientT]:
    def decorator(cls: ClientT) -> ClientT:
        try:
            llm_registry.register(cls, models)
            return cls
        except LLMConfigurationError:
            raise
        except Exception as exc:
            logger.error(
                "Failed to register LLM client %s for %s: %s",
                cls.__name__,
                ", ".join(models),
                exc,
            )
            raise LLMConfigurationError(
                issue=f"Registration failed for {cls.__name__}: {exc}",
                component="client_registration",
            ) from exc

    return decorator
