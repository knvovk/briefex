import logging
from abc import ABC, abstractmethod
from typing import override

from .base import LLMClient
from .exceptions import LLMConfigurationError
from .models import Model
from .registry import llm_registry

logger = logging.getLogger(__name__)

ClientT = type[LLMClient]


class LLMFactory(ABC):

    def __init__(self, *args, **kwargs) -> None:
        self._args = args
        self._kwargs = kwargs

    @abstractmethod
    def create(self, model: Model) -> LLMClient: ...


class DefaultLLMFactory(LLMFactory):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._log_initialization()

    @override
    def create(self, model: Model) -> LLMClient:
        logger.debug("Initializing LLM client for %s", model)
        cls = self._get_client_class(model)
        return self._instantiate_client(cls, model)

    def _get_client_class(self, model: Model) -> ClientT:
        for cls, models in llm_registry.items():
            if model in models:
                return cls

        available_clients = llm_registry.get_client_names()
        clients_str = ", ".join(available_clients) if available_clients else "None"
        raise LLMConfigurationError(
            issue=f"No LLM client registered for {model}. "
            f"Available clients: {clients_str}",
            component="client_selection",
        )

    def _instantiate_client(self, cls: ClientT, model: Model) -> LLMClient:
        try:
            client = cls(*self._args, **self._kwargs)
            logger.info("%s initialized for %s", cls.__name__, model)
            return client
        except Exception as exc:
            logger.error("Failed to instantiate %s: %s", cls.__name__, exc)
            raise LLMConfigurationError(
                issue=f"Client instantiation failed for {cls.__name__}: {exc}",
                component="client_instantiation",
            ) from exc

    def _log_initialization(self) -> None:
        client_count = len(llm_registry)
        if client_count == 0:
            logger.warning("LLMFactory initialized with no registered clients")
            return

        client_names = llm_registry.get_client_names()
        logger.info(
            "LLMFactory initialized with %d client%s: %s",
            client_count,
            "s" if client_count > 1 else "",
            ", ".join(client_names),
        )


def create_default_llm_factory(*args, **kwargs) -> LLMFactory:
    return DefaultLLMFactory(*args, **kwargs)
