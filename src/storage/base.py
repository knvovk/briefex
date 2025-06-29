from __future__ import annotations

import logging
from typing import Any, Callable, ParamSpec, TypeVar

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .exceptions import ModelNotFoundError, handle_integrity_err, map_sqlalchemy_error
from .session import ensure_session

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


class Storage[T]:

    def __init__(self, model: type[T]) -> None:
        self._model: type[T] = model
        logger.debug(
            "%s initialized for model '%s'",
            self.__class__.__name__,
            self._model.__name__,
        )

    @ensure_session
    def add(self, obj: T, *, session: Session) -> T:
        return self._execute(lambda: self._add_func(obj, session))

    @ensure_session
    def add_many(self, objs: list[T], *, session: Session) -> list[T]:
        return self._execute(lambda: self._add_many_func(objs, session))

    @ensure_session
    def get(self, pk: Any, *, session: Session) -> T:
        return self._execute(lambda: self._get_func(pk, session))

    @ensure_session
    def get_many(
        self,
        filters: dict[str, Any] | None = None,
        *,
        session: Session,
    ) -> list[T]:
        return self._execute(lambda: self._get_many_func(filters or {}, session))

    @ensure_session
    def update(self, pk: Any, data: dict[str, Any], *, session: Session) -> T:
        return self._execute(lambda: self._update_func(pk, data, session))

    @ensure_session
    def delete(self, pk: Any, *, session: Session) -> None:
        self._execute(lambda: self._delete_func(pk, session))
        return None

    def _execute(self, operation: Callable[[], R]) -> R:  # noqa
        try:
            return operation()

        except IntegrityError as exc:
            logger.debug("IntegrityError caught: %s", exc, exc_info=True)
            handle_integrity_err(exc)

        except Exception as exc:
            logger.error("Unexpected error: %s", exc, exc_info=True)
            raise map_sqlalchemy_error(exc) from exc

    def _add_func(self, obj: T, session: Session) -> T:  # noqa
        logger.debug("Adding '%s' object to session", self._model.__name__)
        session.add(obj)
        logger.debug("'%s' object successfully added to session", self._model.__name__)
        return obj

    def _add_many_func(self, objs: list[T], session: Session) -> list[T]:  # noqa
        logger.debug(
            "Adding %d '%s' objects to session: %s",
            len(objs),
            self._model.__name__,
        )
        session.add_all(objs)
        logger.debug(
            "%d '%s' objects successfully added to session",
            len(objs),
            self._model.__name__,
        )
        return objs

    def _get_func(self, pk: Any, session: Session) -> T:
        logger.debug("Retrieving '%s' object with id=%s", self._model.__name__, pk)
        instance = session.get(self._model, pk)
        if not instance:
            raise ModelNotFoundError(name=self._model.__name__, pk=str(pk))
        logger.debug("'%s' object successfully retrieved", self._model.__name__)
        return instance

    def _get_many_func(self, filters: dict[str, Any], session: Session) -> list[T]:
        logger.debug(
            "Retrieving '%s' objects with filters: %s",
            self._model.__name__,
            filters,
        )
        query = session.query(self._model).filter_by(**filters)
        objs: list[T] = list(query.all())
        logger.debug(
            "%d '%s' objects successfully retrieved",
            len(objs),
            self._model.__name__,
        )
        return objs

    def _update_func(self, pk: Any, data: dict[str, Any], session: Session) -> T:
        logger.debug("Updating '%s' object with id=%s", self._model.__name__, pk)
        instance = self._get_func(pk, session)
        for k, v in data.items():
            setattr(instance, k, v)
        logger.debug("'%s' object successfully updated", self._model.__name__)
        return instance

    def _delete_func(self, pk: Any, session: Session) -> None:
        logger.debug("Deleting '%s' object with id=%s", self._model.__name__, pk)
        instance = self._get_func(pk, session)
        session.delete(instance)
        logger.debug("'%s' object successfully deleted", self._model.__name__)
        return None
