import logging
from abc import ABC, abstractmethod
from typing import Callable, override

from .base import Storage
from .exceptions import StorageConfigurationError
from .models import Model

logger = logging.getLogger(__name__)

ModelT = type[Model]
StorageT = type[Storage]


class StorageRegistry:

    def __init__(self) -> None:
        self._registry: dict[ModelT, StorageT] = {}

    def register(self, model: ModelT, storage_class: StorageT) -> None:
        self._validate_storage_class(storage_class)
        self._registry[model] = storage_class
        logger.debug(
            "%s registered %s for model %s",
            self.__class__.__name__,
            storage_class.__name__,
            model.__name__,
        )

    def get(self, model: ModelT) -> StorageT | None:
        return self._registry.get(model)

    def is_registered(self, model: ModelT) -> bool:
        return model in self._registry

    def get_registered_models(self) -> list[ModelT]:
        return list(self._registry.keys())

    def _validate_storage_class(self, storage_class: StorageT) -> None:  # noqa
        if not isinstance(storage_class, type) or not issubclass(
            storage_class, Storage
        ):
            raise StorageConfigurationError(
                issue=f"Class {storage_class.__name__} must be a subclass of Storage",
                component="storage_registration",
            )


_storage_registry = StorageRegistry()


class StorageFactory(ABC):

    @abstractmethod
    def create(self, model) -> Storage: ...


class DefaultStorageFactory(StorageFactory):

    def __init__(self) -> None:
        super().__init__()
        self._log_initialization()

    @override
    def create(self, model: ModelT) -> Storage:
        logger.debug("Initializing storage for model: '%s'", model.__name__)
        storage_class = self._get_storage_class(model)
        return self._instantiate_storage(storage_class, model)

    def _get_storage_class(self, model: ModelT) -> StorageT | None:  # noqa
        storage_class = _storage_registry.get(model)

        if storage_class is None:
            models = _storage_registry.get_registered_models()
            raise StorageConfigurationError(
                issue=f"No storage registered for model '{model.__name__}'. "
                f"Registered storages: {', '.join(_storage_registry.get(m).__name__ for m in models)}",
                component="storage_selection",
            )
        return storage_class

    def _instantiate_storage(  # noqa
        self,
        storage_class: StorageT,
        model: ModelT,
    ) -> Storage:
        try:
            storage = storage_class()  # noqa
            logger.info(
                "%s initialized for model '%s'",
                storage_class.__name__,
                model.__name__,
            )
            return storage

        except Exception as exc:
            logger.error("Failed to instantiate %s: %s", storage_class.__name__, exc)
            raise StorageConfigurationError(
                issue=f"Storage instantiation failed for {storage_class.__name__}: {exc}",
                component="storage_instantiation",
            ) from exc

    def _log_initialization(self) -> None:  # noqa
        models = _storage_registry.get_registered_models()
        logger.info(
            "StorageFactory initialized with %d registered storages: %s",
            len(models),
            ", ".join(_storage_registry.get(m).__name__ for m in models),
        )


def register(model: ModelT) -> Callable[[StorageT], StorageT]:
    def decorator(storage_class: StorageT) -> StorageT:
        try:
            _storage_registry.register(model, storage_class)
            return storage_class
        except Exception as exc:
            logger.error(
                "Failed to register storage %s for %s: %s",
                storage_class.__name__,
                model.__name__,
                exc,
            )
            raise StorageConfigurationError(
                issue=f"Registration failed for {storage_class.__name__}: {exc}",
                component="storage_registration",
            )

    return decorator


def create_default_storage_factory() -> StorageFactory:
    return DefaultStorageFactory()
