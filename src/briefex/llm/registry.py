from __future__ import annotations

import logging
from collections.abc import Callable, Sequence

from briefex.llm.base import Provider
from briefex.llm.exceptions import LLMConfigurationError
from briefex.llm.models import Model

_log = logging.getLogger(__name__)


class ProviderRegistry(dict[type[Provider], Sequence[Model]]):
    """Map Provider subclasses to their supported models."""

    def register(self, models: Sequence[Model], cls: type[Provider]) -> None:
        """Register a Provider subclass for the given models.

        Args:
            models: Sequence of Model identifiers supported by the provider.
            cls: Provider subclass to register.

        Raises:
            LLMConfigurationError: If cls is not a subclass of Provider.
        """
        if not isinstance(cls, type) or not issubclass(cls, Provider):
            message = f"Cannot register '{cls.__name__}': not a Provider subclass"
            _log.error(message)
            raise LLMConfigurationError(
                issue=message,
                stage="provider_registration",
            )

        self[cls] = models
        _log.info(
            "Provider '%s' successfully registered for models: %s",
            cls.__name__,
            ", ".join(models),
        )


provider_registry = ProviderRegistry()


def register(models: Sequence[Model]) -> Callable[[type[Provider]], type[Provider]]:
    """Create a decorator to register a Provider for given models.

    Args:
        models: Sequence of Model identifiers the provider supports.

    Returns:
        A decorator that registers the decorated Provider subclass.
    """

    def wrapper(cls: type[Provider]) -> type[Provider]:
        """Register the decorated Provider class in the global registry.

        Args:
            cls: Provider subclass to register.

        Returns:
            The original class.

        Raises:
            LLMConfigurationError: If registration fails.
        """
        _log.debug(
            "Attempting to register provider '%s' for models: %s",
            cls.__name__,
            ", ".join(models),
        )
        try:
            provider_registry.register(models, cls)
            _log.debug(
                "Registered provider '%s' for models: %s",
                cls.__name__,
                ", ".join(models),
            )
            return cls

        except LLMConfigurationError:
            raise

        except Exception as exc:
            _log.error(
                "Unexpected error registering provider '%s' for models %s: %s",
                cls.__name__,
                ", ".join(models),
                exc,
            )
            raise LLMConfigurationError(
                issue=f"Registration failed for '{cls.__name__}': {exc}",
                stage="provider_registration",
            ) from exc

    return wrapper
