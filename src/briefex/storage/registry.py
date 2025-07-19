import logging
from collections.abc import Callable

from .base import Storage
from .exceptions import StorageConfigurationError
from .models import Model

logger = logging.getLogger(__name__)


class StorageRegistry(dict[type[Model], type[Storage]]):
    """Registry for mapping model classes to their storage classes.

    This class extends dict to provide a registry that maps model classes to
    their corresponding storage classes. It includes methods for registering
    storage classes and validating them.
    """

    def register(self, model: type[Model], cls: type[Storage]) -> None:
        """Register a storage class for a model.

        Args:
            model: The model class to register a storage for.
            cls: The storage class to register.

        Raises:
            StorageConfigurationError: If the storage class is not valid.
        """
        self._validate_storage_class(cls)
        self[model] = cls
        logger.debug("%s registered for %s", cls.__name__, model.__name__)

    def _validate_storage_class(self, cls: type[Storage]) -> None:
        """Validate that a class is a valid storage class.

        A valid storage class must be a subclass of Storage.

        Args:
            cls: The class to validate.

        Raises:
            StorageConfigurationError: If the class is not a valid storage class.
        """
        if not isinstance(cls, type) or not issubclass(cls, Storage):
            raise StorageConfigurationError(
                issue=f"Class {cls.__name__} must be a subclass of Storage",
                component="storage_registration",
            )

    def get_storage_names(self) -> list[str]:
        """Get the names of all registered storage classes.

        Returns:
            A list of the names of all registered storage classes.
        """
        return [cls.__name__ for cls in self.values()]


storage_registry = StorageRegistry()
"""Global registry for storing model-to-storage mappings."""


def register(model: type[Model]) -> Callable[[type[Storage]], type[Storage]]:
    """Decorator for registering a storage class for a model.

    This decorator registers the decorated class as the storage class
    for the specified model.
    It's typically used to decorate storage classes to associate them
    with model classes.

    Args:
        model: The model class to register a storage for.

    Returns:
        A decorator function that registers the decorated class and returns it.

    Example:
        @register(User)
        class UserStorage(Storage[User]):
            pass
    """

    def decorator(cls: type[Storage]) -> type[Storage]:
        """The actual decorator function.

        Args:
            cls: The storage class to register.

        Returns:
            The registered storage class.

        Raises:
            StorageConfigurationError: If registration fails.
        """
        try:
            storage_registry.register(model, cls)
            return cls
        except StorageConfigurationError:
            raise
        except Exception as exc:
            logger.error("Unexpected error during storage registration: %s", exc)
            raise StorageConfigurationError(
                issue=f"Registration failed for {cls.__name__}: {exc}",
                component="storage_registration",
            )

    return decorator
