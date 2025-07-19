import logging
from abc import ABC, abstractmethod
from typing import override

from ..exceptions import LLMConfigurationError
from ..models import Model
from .base import LLMProvider
from .registry import llm_provider_registry

logger = logging.getLogger(__name__)


class LLMProviderFactory(ABC):
    """Abstract factory for creating LLM providers.

    This class defines the interface for factories that create LLM providers
    for different language models.

    Attributes:
        _kwargs: Provider-specific configuration parameters.
    """

    def __init__(self, **kwargs) -> None:
        """Initialize the LLM provider factory.

        Args:
            **kwargs: Provider-specific configuration parameters.
        """
        self._kwargs = kwargs

    @abstractmethod
    def create(self, model: Model) -> LLMProvider:
        """Create an LLM provider for the specified model.

        Args:
            model: The language model to create a provider for.

        Returns:
            An LLM provider instance for the specified model.

        Raises:
            LLMConfigurationError: If no provider is available for the specified model.
        """
        ...


class LLMProviderFactoryImpl(LLMProviderFactory):
    """Implementation of the LLMProviderFactory interface.

    This class creates LLM providers based on the registered providers in the
    llm_provider_registry.
    """

    def __init__(self, **kwargs) -> None:
        """Initialize the LLM provider factory implementation.

        Args:
            **kwargs: Provider-specific configuration parameters.
        """
        super().__init__(**kwargs)
        self._log_initialization()

    @override
    def create(self, model: Model) -> LLMProvider:
        """Create an LLM provider for the specified model.

        Args:
            model: The language model to create a provider for.

        Returns:
            An LLM provider instance for the specified model.

        Raises:
            LLMConfigurationError: If no provider is available for the specified model
                or if provider instantiation fails.
        """
        logger.debug("Initializing LLM provider for %s", model)
        cls = self._get_provider_class(model)
        return self._instantiate_provider(cls, model)

    def _get_provider_class(self, model: Model) -> type[LLMProvider]:
        """Get the provider class for the specified model.

        Args:
            model: The language model to get a provider class for.

        Returns:
            The provider class for the specified model.

        Raises:
            LLMConfigurationError: If no provider is registered for the specified model.
        """
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
        """Instantiate a provider of the specified class.

        Args:
            cls: The provider class to instantiate.
            model: The language model the provider is for.

        Returns:
            An instance of the specified provider class.

        Raises:
            LLMConfigurationError: If provider instantiation fails.
        """
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
        """Log information about the initialized factory.

        This method logs the number and names of registered providers.
        """
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


def create_llm_provider_factory(**kwargs) -> LLMProviderFactory:
    """Create a factory for LLM providers.

    Args:
        **kwargs: Provider-specific configuration parameters.

    Returns:
        A factory for creating LLM providers.
    """
    return LLMProviderFactoryImpl(**kwargs)
