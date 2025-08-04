from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

from sqlalchemy import exc as sa_exc

from briefex.storage.base import SourceStorage
from briefex.storage.exceptions import (
    DuplicateObjectError,
    ObjectNotFoundError,
    StorageError,
)
from briefex.storage.models import Source
from briefex.storage.session import connect

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session

_log = logging.getLogger(__name__)


class SQLAlchemySourceStorage(SourceStorage):
    """Storage for Source entities using SQLAlchemy ORM."""

    @override
    @connect
    def add(self, obj: Source, *, session: Session) -> Source:
        """Add a Source to storage.

        Args:
            obj: Source instance to add.
            session: SQLAlchemy session to use.

        Returns:
            The added Source instance.

        Raises:
            DuplicateObjectError: If the source violates a uniqueness constraint.
        """
        _log.debug("Adding Source to storage: %r", obj)
        try:
            session.add(obj)
            _log.info("Source added to session (id=%s)", obj.id)
            return obj
        except sa_exc.IntegrityError as exc:
            _log.error("Integrity error adding Source to session: %s", exc)
            raise DuplicateObjectError(
                cls=Source.__name__,
                details={"issue": str(exc), "obj": obj},
            ) from exc

    @override
    @connect
    def add_all(self, objs: list[Source], *, session: Session) -> list[Source]:
        """Add multiple Source instances to storage.

        Args:
            objs: List of Source instances to add.
            session: SQLAlchemy session to use.

        Returns:
            The list of added Source instances.

        Raises:
            DuplicateObjectError: If any source violates a uniqueness constraint.
        """
        count = len(objs)
        _log.debug("Adding %d Sources to storage", count)
        try:
            session.add_all(objs)
            _log.info("%d Sources added to session", count)
            return objs
        except sa_exc.IntegrityError as exc:
            _log.error("Integrity error adding %d Sources: %s", count, exc)
            raise DuplicateObjectError(
                cls=Source.__name__,
                details={"issue": str(exc), "objs": objs},
            ) from exc

    @override
    @connect
    def get(self, pk: uuid.UUID, *, session: Session) -> Source:
        """Retrieve a Source by primary key.

        Args:
            pk: UUID of the Source to retrieve.
            session: SQLAlchemy session to use.

        Returns:
            The retrieved Source instance.

        Raises:
            ObjectNotFoundError: If no Source with the given pk exists.
            StorageException: On unexpected errors.
        """
        _log.debug("Retrieving Source from storage (pk=%s)", pk)
        try:
            instance = session.get_one(Source, pk)
            _log.info("Source retrieved (pk=%s)", pk)
            return instance
        except sa_exc.NoResultFound as exc:
            _log.warning("No Source found with pk=%s", pk)
            raise ObjectNotFoundError(
                cls=Source.__name__,
                details={"pk": pk},
            ) from exc
        except Exception as exc:
            _log.error("Error retrieving Source (pk=%s): %s", pk, exc)
            raise StorageError(
                message=f"Error retrieving Source with pk={pk}: {exc}",
                details={"pk": pk},
            ) from exc

    @override
    @connect
    def get_all(self, filters: dict | None = None, *, session: Session) -> list[Source]:
        """Retrieve all Sources matching the provided filters.

        Args:
            filters: Dictionary of field-value pairs to filter.
            session: SQLAlchemy session to use.

        Returns:
            List of matching Source instances.

        Raises:
            StorageException: On unexpected errors.
        """
        filters = filters or {}
        _log.debug("Querying Sources with filters: %r", filters)
        try:
            query = session.query(Source).filter_by(**filters)
            objs = list(query.all())
            _log.info("Retrieved %d Sources with filters %r", len(objs), filters)
            return objs
        except Exception as exc:
            _log.error("Error querying Sources with filters %r: %s", filters, exc)
            raise StorageError(
                message=f"Error retrieving Sources: {exc}",
                details={"filters": filters},
            ) from exc

    @override
    @connect
    def update(self, pk: uuid.UUID, data: dict, *, session: Session) -> Source:
        """Update a Source's fields and return the updated instance.

        Args:
            pk: UUID of the Source to update.
            data: Dictionary of field-value pairs to update.
            session: SQLAlchemy session to use.

        Returns:
            The updated Source instance.

        Raises:
            ObjectNotFoundError: If no Source with the given pk exists.
            StorageException: On unexpected errors.
        """
        _log.debug("Updating Source (pk=%s) with data: %r", pk, data)
        try:
            instance = self.get(pk, session=session)
            for key, value in data.items():
                setattr(instance, key, value)
            _log.info("Source updated (pk=%s)", pk)
            return instance
        except ObjectNotFoundError:
            raise
        except Exception as exc:
            _log.error("Error updating Source (pk=%s): %s", pk, exc)
            raise StorageError(
                message=f"Error updating Source with pk={pk}: {exc}",
                details={"pk": pk, "data": data},
            ) from exc

    @override
    @connect
    def delete(self, pk: uuid.UUID, *, session: Session) -> None:
        """Delete a Source by primary key.

        Args:
            pk: UUID of the Source to delete.
            session: SQLAlchemy session to use.

        Raises:
            ObjectNotFoundError: If no Source with the given pk exists.
            StorageException: On unexpected errors.
        """
        _log.debug("Deleting Source (pk=%s)", pk)
        try:
            instance = self.get(pk, session=session)
            session.delete(instance)
            _log.info("Source deleted (pk=%s)", pk)
        except ObjectNotFoundError:
            raise
        except Exception as exc:
            _log.error("Error deleting Source (pk=%s): %s", pk, exc)
            raise StorageError(
                message=f"Error deleting Source with pk={pk}: {exc}",
                details={"pk": pk},
            ) from exc
