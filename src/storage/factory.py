import logging
from abc import ABC, abstractmethod
from typing import override

from .base import Storage
from .exceptions import StorageConfigurationError
from .models import Model
from .registry import storage_registry

logger = logging.getLogger(__name__)

ModelT = type[Model]
StorageT = type[Storage]


class StorageFactory(ABC):

    @abstractmethod
    def create(self, model: ModelT) -> Storage: ...


class StorageFactoryImpl(StorageFactory):

    def __init__(self) -> None:
        super().__init__()
        self._log_initialization()

    @override
    def create(self, model: ModelT) -> Storage:
        logger.debug("Initializing storage for %s", model.__name__)
        cls = self._get_storage_class(model)
        return self._instantiate_storage(cls, model)

    def _get_storage_class(self, model: ModelT) -> StorageT | None:
        if model not in storage_registry:
            available_storages = storage_registry.get_storage_names()
            storages_str = (
                ", ".join(available_storages) if available_storages else "None"
            )
            raise StorageConfigurationError(
                issue=f"No storage registered for {model.__name__}. "
                f"Available storages: {storages_str}",
                component="storage_selection",
            )

        return storage_registry[model]

    def _instantiate_storage(self, cls: StorageT, model: ModelT) -> Storage:
        try:
            storage = cls()
            logger.info("%s initialized for %s", cls.__name__, model.__name__)
            return storage
        except Exception as exc:
            logger.error("Failed to instantiate %s: %s", cls.__name__, exc)
            raise StorageConfigurationError(
                issue=f"Storage instantiation failed for {cls.__name__}: {exc}",
                component="storage_instantiation",
            ) from exc

    def _log_initialization(self) -> None:
        storage_count = len(storage_registry)
        if storage_count == 0:
            logger.warning("StorageFactory initialized with no registered storages")
            return

        storage_names = storage_registry.get_storage_names()
        logger.info(
            "StorageFactory initialized with %d storage%s: %s",
            storage_count,
            "s" if storage_count > 1 else "",
            ", ".join(storage_names),
        )


def create_storage_factory() -> StorageFactory:
    return StorageFactoryImpl()
