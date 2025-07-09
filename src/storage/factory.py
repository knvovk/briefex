import logging
from abc import ABC, abstractmethod
from typing import override

from .base import Storage
from .exceptions import StorageConfigurationError
from .models import Model
from .registry import storage_registry

logger = logging.getLogger(__name__)


class StorageFactory(ABC):
    """Abstract base class for storage factory implementations.

    A storage factory is responsible for creating
    storage instances for different model types.
    """

    @abstractmethod
    def create(self, model: type[Model]) -> Storage:
        """Create a storage instance for the given model type.

        Args:
            model: The model class for which to create a storage.

        Returns:
            A storage instance for the given model.

        Raises:
            StorageConfigurationError: If no storage is registered for the model
                or if storage instantiation fails.
        """
        ...


class StorageFactoryImpl(StorageFactory):
    """Concrete implementation of the StorageFactory interface.

    This class creates storage instances based on the registered storage classes
    in the storage registry.
    """

    def __init__(self) -> None:
        """Initialize a new StorageFactoryImpl instance.

        Logs information about the registered storages during initialization.
        """
        super().__init__()
        self._log_initialization()

    @override
    def create(self, model: type[Model]) -> Storage:
        """Create a storage instance for the given model type.

        Args:
            model: The model class for which to create a storage.

        Returns:
            A storage instance for the given model.

        Raises:
            StorageConfigurationError: If no storage is registered for the model
                or if storage instantiation fails.
        """
        logger.debug("Initializing storage for %s", model.__name__)
        cls = self._get_storage_class(model)
        return self._instantiate_storage(cls, model)

    def _get_storage_class(self, model: type[Model]) -> type[Storage] | None:
        """Get the storage class registered for the given model type.

        Args:
            model: The model class for which to get the storage class.

        Returns:
            The storage class registered for the model.

        Raises:
            StorageConfigurationError: If no storage is registered for the model.
        """
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

    def _instantiate_storage(self, cls: type[Storage], model: type[Model]) -> Storage:
        """Instantiate a storage object of the given class.

        Args:
            cls: The storage class to instantiate.
            model: The model class for which the storage is being instantiated.

        Returns:
            An instance of the storage class.

        Raises:
            StorageConfigurationError: If storage instantiation fails.
        """
        try:
            storage = cls()
            logger.info("%s initialized for %s", cls.__name__, model.__name__)
            return storage
        except Exception as exc:
            logger.error("Unexpected error during storage instantiation: %s", exc)
            raise StorageConfigurationError(
                issue=f"Storage instantiation failed for {cls.__name__}: {exc}",
                component="storage_instantiation",
            ) from exc

    def _log_initialization(self) -> None:
        """Log information about the registered storages during initialization.

        Logs a warning if no storages are registered, or an info message with the
        count and names of registered storages.
        """
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
    """Create and return a new StorageFactory instance.

    This function serves as a factory for creating StorageFactory objects,
    hiding the concrete implementation details from clients.

    Returns:
        A new StorageFactory instance.
    """
    return StorageFactoryImpl()
