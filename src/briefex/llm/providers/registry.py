import logging
from collections.abc import Callable, Sequence

from ..exceptions import LLMConfigurationError
from ..models import Model
from .base import LLMProvider

logger = logging.getLogger(__name__)


class LLMProviderRegistry(dict[type[LLMProvider], Sequence[Model]]):
    """Registry for LLM providers.

    This class extends dict to provide a registry for LLM providers, mapping
    provider classes to the models they support.
    """

    def register(self, cls: type[LLMProvider], models: Sequence[Model]) -> None:
        """Register an LLM provider class for the specified models.

        Args:
            cls: The LLM provider class to register.
            models: The models that the provider supports.

        Raises:
            LLMConfigurationError: If the class is not a valid LLM provider class.
        """
        self._validate_provider_class(cls)
        self[cls] = models
        logger.debug("%s registered for %s", cls.__name__, ", ".join(models))

    def _validate_provider_class(self, cls: type[LLMProvider]) -> None:
        """Validate that a class is a valid LLM provider class.

        Args:
            cls: The class to validate.

        Raises:
            LLMConfigurationError: If the class is not a valid LLM provider class.
        """
        if not isinstance(cls, type) or not issubclass(cls, LLMProvider):
            raise LLMConfigurationError(
                issue=f"Class {cls.__name__} must be a subclass of LLMProvider",
                component="provider_registration",
            )

    def get_provider_names(self) -> list[str]:
        """Get the names of all registered provider classes.

        Returns:
            A list of provider class names.
        """
        return [cls.__name__ for cls in self.keys()]


llm_provider_registry = LLMProviderRegistry()
"""Global registry for LLM providers."""


def register(
    models: Sequence[Model],
) -> Callable[[type[LLMProvider]], type[LLMProvider]]:
    """Decorator for registering LLM provider classes.

    This decorator registers an LLM provider class with the global registry
    for the specified models.

    Args:
        models: The models that the provider supports.

    Returns:
        A decorator function that registers the decorated class.

    Raises:
        LLMConfigurationError: If registration fails.
    """

    def decorator(cls: type[LLMProvider]) -> type[LLMProvider]:
        """Register the decorated class with the registry.

        Args:
            cls: The LLM provider class to register.

        Returns:
            The registered class.

        Raises:
            LLMConfigurationError: If registration fails.
        """
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
