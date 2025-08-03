from __future__ import annotations

import logging
from typing import override

from briefex.llm.base import Provider, ProviderFactory
from briefex.llm.exceptions import LLMConfigurationError
from briefex.llm.models import Model
from briefex.llm.registry import provider_registry

_log = logging.getLogger(__name__)


class DefaultProviderFactory(ProviderFactory):
    """Factory that selects and instantiates a Provider based on a Model."""

    @override
    def create(self, model: Model) -> Provider:
        """Create a Provider for the given model.

        Args:
            model: Model instance specifying the provider configuration.

        Returns:
            A Provider instance configured for the specified model.

        Raises:
            LLMConfigurationError: If no provider is registered for the model
                or if instantiation fails.
        """
        _log.debug("Initializing provider for %s", model)

        provider_cls: type[Provider] | None = None
        for cls, models in provider_registry.items():
            if model in models:
                provider_cls = cls

        if provider_cls is None:
            raise LLMConfigurationError(
                issue=f"No provider registered for {model}",
                stage="provider_selection",
            )

        try:
            instance = provider_cls(*self._provider_args, **self._provider_kwargs)
            _log.info("%s initialized for %s", provider_cls.__name__, model)
            return instance

        except Exception as exc:
            _log.error("Unexpected error during provider instantiation: %s", exc)
            provider_cls_name = provider_cls.__name__
            raise LLMConfigurationError(
                issue=f"Provider instantiation failed for {provider_cls_name}: {exc}",
                stage="provider_instantiation",
            ) from exc
