from __future__ import annotations

import logging
from typing import Any, Callable, ParamSpec, TypeVar

from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from .exceptions import (
    ModelNotFoundError,
    QueryExecutionError,
    StorageConnectionError,
    create_from_integrity_err,
)
from .session import inject_session

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


class Storage[T]:
    """Base storage class for database operations.

    This class provides basic CRUD operations for database models.

    Args:
        model: The SQLAlchemy model class to operate on.
    """

    def __init__(self, model: type[T]) -> None:
        """Initialize the storage with a model class.

        Args:
            model: The SQLAlchemy model class to operate on.
        """
        self._model: type[T] = model

    @inject_session
    def add(self, obj: T, *, session: Session) -> T:
        """Add a single object to the database.

        Args:
            obj: The object to add.
            session: The database session to use.

        Returns:
            The added object.

        Raises:
            StorageException: If there's an error during the operation.
        """
        return self._execute(lambda: self._add_func(obj, session))

    @inject_session
    def add_many(self, objs: list[T], *, session: Session) -> list[T]:
        """Add multiple objects to the database.

        Args:
            objs: A list of objects to add.
            session: The database session to use.

        Returns:
            The list of added objects.

        Raises:
            StorageException: If there's an error during the operation.
        """
        return self._execute(lambda: self._add_many_func(objs, session))

    @inject_session
    def get(self, pk: Any, *, session: Session) -> T:
        """Retrieve a single object by its primary key.

        Args:
            pk: The primary key of the object to retrieve.
            session: The database session to use.

        Returns:
            The retrieved object.

        Raises:
            ModelNotFoundError: If the object with the given primary key doesn't exist.
            StorageException: If there's an error during the operation.
        """
        return self._execute(lambda: self._get_func(pk, session))

    @inject_session
    def get_many(
        self,
        filters: dict[str, Any] | None = None,
        *,
        session: Session,
    ) -> list[T]:
        """Retrieve multiple objects based on filters.

        Args:
            filters: A dictionary of attribute-value pairs to filter objects by.
                If None, all objects of the model type are returned.
            session: The database session to use.

        Returns:
            A list of objects matching the filters.

        Raises:
            StorageException: If there's an error during the operation.
        """
        return self._execute(lambda: self._get_many_func(filters or {}, session))

    @inject_session
    def update(self, pk: Any, data: dict[str, Any], *, session: Session) -> T:
        """Update an object by its primary key.

        Args:
            pk: The primary key of the object to update.
            data: A dictionary of attribute-value pairs to update.
            session: The database session to use.

        Returns:
            The updated object.

        Raises:
            ModelNotFoundError: If the object with the given primary key doesn't exist.
            StorageException: If there's an error during the operation.
        """
        return self._execute(lambda: self._update_func(pk, data, session))

    @inject_session
    def delete(self, pk: Any, *, session: Session) -> None:
        """Delete an object by its primary key.

        Args:
            pk: The primary key of the object to delete.
            session: The database session to use.

        Raises:
            ModelNotFoundError: If the object with the given primary key doesn't exist.
            StorageException: If there's an error during the operation.
        """
        self._execute(lambda: self._delete_func(pk, session))
        return None

    def _execute(self, operation: Callable[[], R]) -> R:
        """Execute a database operation with error handling.

        Args:
            operation: A callable that performs the database operation.

        Returns:
            The result of the operation.

        Raises:
            StorageException: If there's an error during the operation.
        """
        try:
            return operation()
        except IntegrityError as exc:
            logger.error("IntegrityError caught: %s", exc, exc_info=True)
            create_from_integrity_err(exc)
        except OperationalError as exc:
            logger.error("OperationalError caught: %s", exc, exc_info=True)
            raise StorageConnectionError(
                details={
                    "reason": str(exc),
                }
            ) from exc
        except Exception as exc:
            logger.error("Unexpected error during operation: %s", exc)
            raise QueryExecutionError(reason=str(exc)) from exc

    def _add_func(self, obj: T, session: Session) -> T:
        """Internal method to add a single object to the session.

        Args:
            obj: The object to add.
            session: The database session to use.

        Returns:
            The added object.
        """
        logger.debug("Adding %s object to session", self._model.__name__)
        session.add(obj)
        logger.info("%s object added to session", self._model.__name__)
        return obj

    def _add_many_func(self, objs: list[T], session: Session) -> list[T]:
        """Internal method to add multiple objects to the session.

        Args:
            objs: A list of objects to add.
            session: The database session to use.

        Returns:
            The list of added objects.
        """
        logger.debug(
            "Adding %d %s objects to session: %s",
            len(objs),
            self._model.__name__,
        )
        session.add_all(objs)
        logger.info(
            "%d %s objects added to session",
            len(objs),
            self._model.__name__,
        )
        return objs

    def _get_func(self, pk: Any, session: Session) -> T:
        """Internal method to retrieve a single object by its primary key.

        Args:
            pk: The primary key of the object to retrieve.
            session: The database session to use.

        Returns:
            The retrieved object.

        Raises:
            ModelNotFoundError: If the object with the given primary key doesn't exist.
        """
        logger.debug("Retrieving %s object with id=%s", self._model.__name__, pk)
        instance = session.get(self._model, pk)
        if not instance:
            raise ModelNotFoundError(name=self._model.__name__, pk=str(pk))
        logger.info("%s object with id=%s retrieved", self._model.__name__, pk)
        return instance

    def _get_many_func(self, filters: dict[str, Any], session: Session) -> list[T]:
        """Internal method to retrieve multiple objects based on filters.

        Args:
            filters: A dictionary of attribute-value pairs to filter objects by.
            session: The database session to use.

        Returns:
            A list of objects matching the filters.
        """
        logger.debug(
            "Retrieving %s objects with filters=%s",
            self._model.__name__,
            filters,
        )
        query = session.query(self._model).filter_by(**filters)
        objs: list[T] = list(query.all())
        logger.info("%d %s objects retrieved", len(objs), self._model.__name__)
        return objs

    def _update_func(self, pk: Any, data: dict[str, Any], session: Session) -> T:
        """Internal method to update an object by its primary key.

        Args:
            pk: The primary key of the object to update.
            data: A dictionary of attribute-value pairs to update.
            session: The database session to use.

        Returns:
            The updated object.

        Raises:
            ModelNotFoundError: If the object with the given primary key doesn't exist.
        """
        logger.debug("Updating %s object with id=%s", self._model.__name__, pk)
        instance = self._get_func(pk, session)
        for k, v in data.items():
            setattr(instance, k, v)
        logger.info("%s object with id=%s updated", self._model.__name__, pk)
        return instance

    def _delete_func(self, pk: Any, session: Session) -> None:
        """Internal method to delete an object by its primary key.

        Args:
            pk: The primary key of the object to delete.
            session: The database session to use.

        Raises:
            ModelNotFoundError: If the object with the given primary key doesn't exist.
        """
        logger.debug("Deleting %s object with id=%s", self._model.__name__, pk)
        instance = self._get_func(pk, session)
        session.delete(instance)
        logger.info("%s object with id=%s deleted", self._model.__name__, pk)
        return None
