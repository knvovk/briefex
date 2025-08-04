from __future__ import annotations

import datetime
import logging
import uuid
from typing import override

from sqlalchemy import exc as sa_exc
from sqlalchemy import select
from sqlalchemy.orm import Session

from briefex.storage.base import PostStorage
from briefex.storage.exceptions import (
    DuplicateObjectError,
    ObjectNotFoundError,
    StorageException,
)
from briefex.storage.models import Post
from briefex.storage.session import connect

_log = logging.getLogger(__name__)


class SQLAlchemyPostStorage(PostStorage):
    """Storage for Post entities using SQLAlchemy ORM."""

    @override
    @connect
    def add(self, obj: Post, *, session: Session) -> Post:
        """Add a Post to storage.

        Args:
            obj: Post instance to add.
            session: SQLAlchemy session to use.

        Returns:
            The added Post instance.

        Raises:
            DuplicateObjectError: If the post violates a uniqueness constraint.
        """
        _log.debug("Adding Post to storage: %r", obj)
        try:
            session.add(obj)
            _log.info("Post added to session (id=%s)", obj.id)
            return obj
        except sa_exc.IntegrityError as exc:
            _log.error("Integrity error adding Post to session: %s", exc)
            raise DuplicateObjectError(
                cls=Post.__name__,
                details={"issue": str(exc), "obj": obj},
            ) from exc

    @override
    @connect
    def add_all(self, objs: list[Post], *, session: Session) -> list[Post]:
        """Add multiple Post instances to storage.

        Args:
            objs: List of Post instances to add.
            session: SQLAlchemy session to use.

        Returns:
            The list of added Post instances.

        Raises:
            DuplicateObjectError: If any post violates a uniqueness constraint.
        """
        count = len(objs)
        _log.debug("Adding %d Posts to storage", count)
        try:
            session.add_all(objs)
            _log.info("%d Posts added to session", count)
            return objs
        except sa_exc.IntegrityError as exc:
            _log.error("Integrity error adding Posts to session: %s", exc)
            raise DuplicateObjectError(
                cls=Post.__name__,
                details={"issue": str(exc), "objs": objs},
            ) from exc

    @override
    @connect
    def get(self, pk: uuid.UUID, *, session: Session) -> Post:
        """Retrieve a Post by primary key.

        Args:
            pk: UUID of the Post to retrieve.
            session: SQLAlchemy session to use.

        Returns:
            The retrieved Post instance.

        Raises:
            ObjectNotFoundError: If no Post with the given pk exists.
            StorageException: On unexpected errors.
        """
        _log.debug("Retrieving Post from storage (pk=%s)", pk)
        try:
            instance = session.get_one(Post, pk)
            _log.info("Post retrieved from storage (pk=%s)", pk)
            return instance
        except sa_exc.NoResultFound as exc:
            _log.warning("No Post found with pk=%s", pk)
            raise ObjectNotFoundError(
                cls=Post.__name__,
                details={"pk": pk},
            ) from exc
        except Exception as exc:
            _log.error("Error retrieving Post (pk=%s): %s", pk, exc)
            raise StorageException(
                message=f"Error retrieving Post with pk={pk}: {exc}",
                details={"pk": pk},
            ) from exc

    @override
    @connect
    def get_recent(self, days: int, *, session: Session) -> list[Post]:
        """Retrieve Posts published within the last given number of days.

        Args:
            days: Number of days to look back.
            session: SQLAlchemy session to use.

        Returns:
            List of Post instances.

        Raises:
            StorageException: On unexpected errors.
        """
        _log.debug("Querying recent Posts (days=%d)", days)
        try:
            cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=days)
            query = (
                select(Post)
                .where(Post.created_at >= cutoff)
                .order_by(Post.created_at.desc())
            )
            objs = list(session.scalars(query).all())
            _log.info(
                "Retrieved %d recent Posts (days=%d)",
                len(objs),
                days,
            )
            return objs
        except Exception as exc:
            _log.error("Error querying recent Posts (days=%d): %s", days, exc)
            raise StorageException(
                message=f"Error retrieving recent Posts: {exc}",
                details={"days": days},
            ) from exc

    @override
    @connect
    def get_all(self, filters: dict | None = None, *, session: Session) -> list[Post]:
        """Retrieve all Posts matching the provided filters.

        Args:
            filters: Dictionary of field-value pairs to filter.
            session: SQLAlchemy session to use.

        Returns:
            List of matching Post instances.

        Raises:
            StorageException: On unexpected errors.
        """
        filters = filters or {}
        _log.debug("Querying all Posts with filters: %r", filters)
        try:
            query = session.query(Post).filter_by(**filters)
            objs = list(query.all())
            _log.info(
                "Retrieved %d Posts with filters %r",
                len(objs),
                filters,
            )
            return objs
        except Exception as exc:
            _log.error("Error querying Posts with filters %r: %s", filters, exc)
            raise StorageException(
                message=f"Error retrieving Posts: {exc}",
                details={"filters": filters},
            ) from exc

    @override
    @connect
    def update(self, pk: uuid.UUID, data: dict, *, session: Session) -> Post:
        """Update a Post's fields and return the updated instance.

        Args:
            pk: UUID of the Post to update.
            data: Dictionary of field-value pairs to update.
            session: SQLAlchemy session to use.

        Returns:
            The updated Post instance.

        Raises:
            ObjectNotFoundError: If no Post with the given pk exists.
            StorageException: On unexpected errors.
        """
        _log.debug("Updating Post (pk=%s) with data: %r", pk, data)
        try:
            instance = self.get(pk, session=session)
            for key, value in data.items():
                setattr(instance, key, value)
            _log.info("Post updated (pk=%s)", pk)
            return instance
        except ObjectNotFoundError:
            raise
        except Exception as exc:
            _log.error("Error updating Post (pk=%s): %s", pk, exc)
            raise StorageException(
                message=f"Error updating Post with pk={pk}: {exc}",
                details={"pk": pk, "data": data},
            ) from exc

    @override
    @connect
    def delete(self, pk: uuid.UUID, *, session: Session) -> None:
        """Delete a Post by primary key.

        Args:
            pk: UUID of the Post to delete.
            session: SQLAlchemy session to use.

        Raises:
            ObjectNotFoundError: If no Post with the given pk exists.
            StorageException: On unexpected errors.
        """
        _log.debug("Deleting Post (pk=%s)", pk)
        try:
            instance = self.get(pk, session=session)
            session.delete(instance)
            _log.info("Post deleted (pk=%s)", pk)
        except ObjectNotFoundError:
            raise
        except Exception as exc:
            _log.error("Error deleting Post (pk=%s): %s", pk, exc)
            raise StorageException(
                message=f"Error deleting Post with pk={pk}: {exc}",
                details={"pk": pk},
            ) from exc
