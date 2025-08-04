from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session

    from briefex.storage.models import Post, Source

_log = logging.getLogger(__name__)


class SourceStorage(ABC):
    """Interface for CRUD operations on Source entities."""

    @abstractmethod
    def add(self, obj: Source, *, session: Session) -> Source:
        """Add a Source record and return the persisted instance."""

    @abstractmethod
    def add_all(self, objs: list[Source], *, session: Session) -> list[Source]:
        """Add multiple Source records and return the persisted instances."""

    @abstractmethod
    def get(self, pk: uuid.UUID, *, session: Session) -> Source:
        """Retrieve a Source by its primary key."""

    @abstractmethod
    def get_all(self, filters: dict | None = None, *, session: Session) -> list[Source]:
        """Retrieve all Sources matching given filters."""

    @abstractmethod
    def update(self, pk: uuid.UUID, data: dict, *, session: Session) -> Source:
        """Update a Source record and return the updated instance."""

    @abstractmethod
    def delete(self, pk: uuid.UUID, *, session: Session) -> None:
        """Delete a Source by its primary key."""


class PostStorage(ABC):
    """Interface for CRUD operations on Post entities."""

    @abstractmethod
    def add(self, obj: Post, *, session: Session) -> Post:
        """Add a Post record and return the persisted instance."""

    @abstractmethod
    def add_all(self, objs: list[Post], *, session: Session) -> list[Post]:
        """Add multiple Post records and return the persisted instances."""

    @abstractmethod
    def get(self, pk: uuid.UUID, *, session: Session) -> Post:
        """Retrieve a Post by its primary key."""

    @abstractmethod
    def get_recent(self, days: int, *, session: Session) -> list[Post]:
        """Retrieve Posts published within the last given number of days."""

    @abstractmethod
    def get_all(self, filters: dict | None = None, *, session: Session) -> list[Post]:
        """Retrieve all Posts matching given filters."""

    @abstractmethod
    def update(self, pk: uuid.UUID, data: dict, *, session: Session) -> Post:
        """Update a Post by its primary key with provided data and return it."""

    @abstractmethod
    def delete(self, pk: uuid.UUID, *, session: Session) -> None:
        """Delete a Post by its primary key."""


class SourceStorageFactory(ABC):
    """Factory interface for creating SourceStorage instances."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._storage_args = args
        self._storage_kwargs = kwargs

        _log.info(
            "%s initialized with args=%r, kwargs=%r",
            self.__class__.__name__,
            self._storage_args,
            self._storage_kwargs,
        )

    @abstractmethod
    def create(self) -> SourceStorage:
        """Create and return a new SourceStorage instance."""


class PostStorageFactory(ABC):
    """Factory interface for creating PostStorage instances."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._storage_args = args
        self._storage_kwargs = kwargs

        _log.info(
            "%s initialized with args=%r, kwargs=%r",
            self.__class__.__name__,
            self._storage_args,
            self._storage_kwargs,
        )

    @abstractmethod
    def create(self) -> PostStorage:
        """Create and return a new PostStorage instance."""
