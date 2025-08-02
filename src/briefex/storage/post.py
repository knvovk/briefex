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
        _log.debug("Adding new post to storage")

        try:
            session.add(obj)
        except sa_exc.IntegrityError as exc:
            _log.error("Integrity error during adding post to session: %s", exc)
            raise DuplicateObjectError(
                cls=Post.__class__.__name__,
                details={
                    "issue": str(exc),
                    "obj": obj,
                },
            ) from exc

        _log.debug("Successfully added new post to storage")
        return obj

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
        _log.debug("Adding all new posts to storage")

        try:
            session.add_all(objs)
        except sa_exc.IntegrityError as exc:
            _log.error("Integrity error during adding posts to session: %s", exc)
            raise DuplicateObjectError(
                cls=Post.__class__.__name__,
                details={
                    "issue": str(exc),
                    "objs": objs,
                },
            ) from exc

        _log.debug("Successfully added all new posts to storage")
        return objs

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
        _log.debug("Retrieving post from storage (pk: %s)", pk)

        try:
            instance = session.get_one(Post, pk)
            _log.debug("Successfully retrieved post from storage (pk: %s)", pk)
            return instance

        except sa_exc.NoResultFound as exc:
            raise ObjectNotFoundError(
                cls=Post.__class__.__name__,
                details={
                    "pk": pk,
                },
            ) from exc

        except Exception as exc:
            _log.error(
                "Unexpected error during retrieving post from storage: %s",
                exc,
            )
            raise StorageException(
                message=f"Unexpected error during retrieving post from storage: {exc}",
                details={
                    "pk": pk,
                },
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
        _log.debug("Retrieving recent posts from storage (days: %d)", days)

        try:
            cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=days)
            query = (
                select(Post)
                .where(Post.created_at >= cutoff)
                .order_by(Post.created_at.desc())
            )
            objs = list(session.scalars(query).all())

            _log.debug(
                "Successfully retrieved %d recent posts from storage (days: %d)",
                len(objs),
                days,
            )
            return objs

        except Exception as exc:
            _log.error(
                "Unexpected error during retrieving recent posts from storage: %s",
                exc,
            )
            raise StorageException(
                message=(
                    f"Unexpected error during retrieving "
                    f"recent posts from storage: {exc}"
                ),
                details={
                    "days": days,
                },
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
        _log.debug("Retrieving all posts from storage (filters: %r)", filters)

        try:
            filters = filters or {}
            query = session.query(Post).filter_by(**filters)
            objs = list(query.all())

            _log.debug(
                "Successfully retrieved %d posts from storage (filters: %r)",
                len(objs),
                filters,
            )
            return objs

        except Exception as exc:
            _log.error(
                "Unexpected error during retrieving all posts from storage: %s",
                exc,
            )
            raise StorageException(
                message=(
                    f"Unexpected error during retrieving "
                    f"all posts from storage: {exc}"
                ),
                details={
                    "filters": filters,
                },
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
        _log.debug("Updating post from storage (pk: %s)", pk)

        try:
            instance = self.get(pk, session=session)
            for k, v in data.items():
                setattr(instance, k, v)

            _log.debug("Successfully updated post from storage (pk: %s)", pk)
            return instance

        except ObjectNotFoundError:
            raise

        except Exception as exc:
            _log.error("Unexpected error during updating post from storage: %s", exc)
            raise StorageException(
                message=f"Unexpected error during updating post from storage: {exc}",
                details={
                    "pk": pk,
                    "data": data,
                },
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
        _log.debug("Deleting post from storage (pk: %s)", pk)

        try:
            instance = self.get(pk, session=session)
            session.delete(instance)
            _log.debug("Successfully deleted post from storage (pk: %s)", pk)

        except ObjectNotFoundError:
            raise

        except Exception as exc:
            _log.error("Unexpected error during deleting post from storage: %s", exc)
            raise StorageException(
                message=f"Unexpected error during deleting post from storage: {exc}",
                details={
                    "pk": pk,
                },
            ) from exc
