import logging
from abc import ABC, abstractmethod
from typing import override

from ..exceptions import LLMConfigurationError
from ..models import Model
from .base import LLMProvider
from .registry import llm_provider_registry

logger = logging.getLogger(__name__)


class LLMProviderFactory(ABC):

    def __init__(self, **kwargs) -> None:
        self._kwargs = kwargs

    @abstractmethod
    def create(self, model: Model) -> LLMProvider: ...


class LLMProviderFactoryImpl(LLMProviderFactory):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._log_initialization()

    @override
    def create(self, model: Model) -> LLMProvider:
        logger.debug("Initializing LLM provider for %s", model)
        cls = self._get_provider_class(model)
        return self._instantiate_provider(cls, model)

    def _get_provider_class(self, model: Model) -> type[LLMProvider]:
        for cls, models in llm_provider_registry.items():
            if model in models:
                return cls

        available_providers = llm_provider_registry.get_provider_names()
        providers_str = (
            ", ".join(available_providers) if available_providers else "None"
        )
        raise LLMConfigurationError(
            issue=f"No LLM provider registered for {model}. "
            f"Available providers: {providers_str}",
            component="provider_selection",
        )

    def _instantiate_provider(
        self,
        cls: type[LLMProvider],
        model: Model,
    ) -> LLMProvider:
        try:
            provider = cls(**self._kwargs)
            logger.info("%s initialized for %s", cls.__name__, model)
            return provider
        except Exception as exc:
            logger.error("Failed to instantiate %s: %s", cls.__name__, exc)
            raise LLMConfigurationError(
                issue=f"Provider instantiation failed for {cls.__name__}: {exc}",
                component="provider_instantiation",
            ) from exc

    def _log_initialization(self) -> None:
        provider_count = len(llm_provider_registry)
        if provider_count == 0:
            logger.warning(
                "LLMProviderFactory initialized with no registered providers"
            )
            return

        provider_names = llm_provider_registry.get_provider_names()
        logger.info(
            "LLMProviderFactory initialized with %d provider%s: %s",
            provider_count,
            "s" if provider_count > 1 else "",
            ", ".join(provider_names),
        )


def create_default_llm_provider_factory(**kwargs) -> LLMProviderFactory:
    return LLMProviderFactoryImpl(**kwargs)
