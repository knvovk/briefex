from __future__ import annotations

import logging
import uuid
from typing import override

from sqlalchemy import exc as sa_exc
from sqlalchemy.orm import Session

from briefex.storage.base import SourceStorage
from briefex.storage.exceptions import (
    DuplicateObjectError,
    ObjectNotFoundError,
    StorageException,
)
from briefex.storage.models import Source
from briefex.storage.session import connect

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
        _log.debug("Adding new source to storage")

        try:
            session.add(obj)
        except sa_exc.IntegrityError as exc:
            _log.error("Integrity error during adding source to session: %s", exc)
            raise DuplicateObjectError(
                cls=Source.__class__.__name__,
                details={
                    "issue": str(exc),
                    "obj": obj,
                },
            ) from exc

        _log.debug("Successfully added new source to storage")
        return obj

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
        _log.debug("Adding all new sources to storage")

        try:
            session.add_all(objs)
        except sa_exc.IntegrityError as exc:
            _log.error("Integrity error during adding sources to session: %s", exc)
            raise DuplicateObjectError(
                cls=Source.__class__.__name__,
                details={
                    "issue": str(exc),
                    "objs": objs,
                },
            ) from exc

        _log.debug("Successfully added all new sources to storage")
        return objs

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
        _log.debug("Retrieving source from storage (pk: %s)", pk)

        try:
            instance = session.get_one(Source, pk)
            _log.debug("Successfully retrieved source from storage (pk: %s)", pk)
            return instance

        except sa_exc.NoResultFound as exc:
            raise ObjectNotFoundError(
                cls=Source.__class__.__name__,
                details={
                    "pk": pk,
                },
            ) from exc

        except Exception as exc:
            _log.error(
                "Unexpected error during retrieving source from storage: %s",
                exc,
            )
            raise StorageException(
                message=(
                    "Unexpected error during retrieving "
                    + f"source from storage: {exc}"
                ),
                details={
                    "pk": pk,
                },
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
        _log.debug("Retrieving all sources from storage (filters: %r)", filters)

        try:
            filters = filters or {}
            query = session.query(Source).filter_by(**filters)
            objs = list(query.all())

            _log.debug(
                "Successfully retrieved %d sources from storage (filters: %r)",
                len(objs),
                filters,
            )
            return objs

        except Exception as exc:
            _log.error(
                "Unexpected error during retrieving all sources from storage: %s",
                exc,
            )
            raise StorageException(
                message=(
                    f"Unexpected error during retrieving "
                    f"all sources from storage: {exc}"
                ),
                details={
                    "filters": filters,
                },
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
        _log.debug("Updating source from storage (pk: %s)", pk)

        try:
            instance = self.get(pk, session=session)
            for k, v in data.items():
                setattr(instance, k, v)

            _log.debug("Successfully updated source from storage (pk: %s)", pk)
            return instance

        except ObjectNotFoundError:
            raise

        except Exception as exc:
            _log.error("Unexpected error during updating source from storage: %s", exc)
            raise StorageException(
                message=f"Unexpected error during updating source from storage: {exc}",
                details={
                    "pk": pk,
                    "data": data,
                },
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
        _log.debug("Deleting source from storage (pk: %s)", pk)

        try:
            instance = self.get(pk, session=session)
            session.delete(instance)
            _log.debug("Successfully deleted source from storage (pk: %s)", pk)

        except ObjectNotFoundError:
            raise

        except Exception as exc:
            _log.error("Unexpected error during deleting source from storage: %s", exc)
            raise StorageException(
                message=f"Unexpected error during deleting source from storage: {exc}",
                details={
                    "pk": pk,
                },
            ) from exc
