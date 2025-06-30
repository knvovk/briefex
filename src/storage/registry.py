import logging
from typing import Callable

from .base import Storage
from .exceptions import StorageConfigurationError
from .models import Model

logger = logging.getLogger(__name__)

ModelT = type[Model]
StorageT = type[Storage]


class StorageRegistry(dict[ModelT, StorageT]):

    def register(self, model: ModelT, cls: StorageT) -> None:
        self._validate_storage_class(cls)
        self[model] = cls
        logger.debug("%s registered for %s", cls.__name__, model.__name__)

    @staticmethod
    def _validate_storage_class(cls: StorageT) -> None:
        if not isinstance(cls, type) or not issubclass(cls, Storage):
            raise StorageConfigurationError(
                issue=f"Class {cls.__name__} must be a subclass of Storage",
                component="storage_registration",
            )

    def get_storage_names(self) -> list[str]:
        return [cls.__name__ for cls in self.values()]


storage_registry = StorageRegistry()


def register(model: ModelT) -> Callable[[StorageT], StorageT]:
    def decorator(cls: StorageT) -> StorageT:
        try:
            storage_registry.register(model, cls)
            return cls
        except StorageConfigurationError:
            raise
        except Exception as exc:
            logger.error(
                "Failed to register storage %s for %s: %s",
                cls.__name__,
                model.__name__,
                exc,
            )
            raise StorageConfigurationError(
                issue=f"Registration failed for {cls.__name__}: {exc}",
                component="storage_registration",
            )

    return decorator
