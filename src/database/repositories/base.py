from __future__ import annotations

import logging
import re
from functools import wraps
from typing import Any, Callable, Generic, ParamSpec, TypeVar

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..exceptions import (
    ConstraintViolationError,
    DuplicateError,
    ModelNotFoundError,
    TransactionError,
)
from ..session import session_scope

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")
ModelT = TypeVar("ModelT")
FilterT = dict[str, Any]

_DUPLICATE_KEY_RE: re.Pattern[str] = re.compile(
    r"duplicate key value violates unique constraint "
    r'".*?_(?P<field>\w+)_key"'
    r".*?Detail:.*?=\s*\((?P<value>.+?)\)",
    re.IGNORECASE | re.DOTALL,
)

_CONSTRAINT_RE: re.Pattern[str] = re.compile(
    r"violates check constraint\s+\"(?P<constraint>[^\"]+)\"", re.IGNORECASE
)


def _log_operation(name: str) -> Callable[[Callable[..., R]], Callable[..., R]]:
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @wraps(func)
        def wrapper(self: BaseRepository, *args: Any, **kwargs: Any) -> R:
            logger.debug(
                "Operation %s started | args=%s | kwargs=%s", name, args, kwargs
            )
            try:
                result: R = func(self, *args, **kwargs)
                logger.info("Operation %s completed successfully", name)
                return result
            except Exception:
                logger.exception("Operation %s failed", name)
                raise

        return wrapper

    return decorator


def ensure_session(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        if kwargs.get("session") is None:
            with session_scope() as session:
                kwargs["session"] = session
                return func(*args, **kwargs)
        return func(*args, **kwargs)

    return wrapper


class BaseRepository(Generic[ModelT]):

    __slots__ = ("_model",)

    def __init__(self, model: type[ModelT]) -> None:
        self._model: type[ModelT] = model
        logger.debug(
            "%s initialized for model '%s'",
            self.__class__.__name__,
            self._model.__name__,
        )

    @_log_operation("add")
    @ensure_session
    def add(self, obj: ModelT, *, session: Session) -> ModelT:
        return self._execute(lambda: self._add_internal(obj, session))

    @_log_operation("add_many")
    @ensure_session
    def add_many(self, objs: list[ModelT], *, session: Session) -> list[ModelT]:
        return self._execute(lambda: self._add_many_internal(objs, session))

    @_log_operation("get")
    @ensure_session
    def get(self, pk: Any, *, session: Session) -> ModelT:
        return self._execute(lambda: self._get_internal(pk, session))

    @_log_operation("list")
    @ensure_session
    def list(self, filters: FilterT | None = None, *, session: Session) -> list[ModelT]:
        return self._execute(lambda: self._list_internal(filters or {}, session))

    @_log_operation("update")
    @ensure_session
    def update(self, pk: Any, data: FilterT, *, session: Session) -> ModelT:
        return self._execute(lambda: self._update_internal(pk, data, session))

    @_log_operation("delete")
    @ensure_session
    def delete(self, pk: Any, *, session: Session) -> None:
        self._execute(lambda: self._delete_internal(pk, session))
        return None

    def _execute(self, action: Callable[[], R]) -> R:
        try:
            return action()
        except IntegrityError as exc:
            logger.debug("IntegrityError caught: %s", exc, exc_info=True)
            self._handle_integrity(exc)
            raise  # не должен сюда дойти
        except Exception as exc:
            logger.error("Unexpected repo error: %s", exc, exc_info=True)
            raise TransactionError(str(exc)) from exc

    def _add_internal(self, obj: ModelT, session: Session) -> ModelT:
        session.add(obj)
        return obj

    def _add_many_internal(self, objs: list[ModelT], session: Session) -> list[ModelT]:
        session.add_all(objs)
        return objs

    def _get_internal(self, pk: Any, session: Session) -> ModelT:
        instance = session.get(self._model, pk)
        if not instance:
            raise ModelNotFoundError(name=self._model.__name__, pk=str(pk))
        return instance

    def _list_internal(self, filters: FilterT, session: Session) -> list[ModelT]:
        query = session.query(self._model).filter_by(**filters)  # type: ignore[arg-type]
        return list(query.all())

    def _update_internal(self, pk: Any, data: FilterT, session: Session) -> ModelT:
        instance = self._get_internal(pk, session)
        for k, v in data.items():
            setattr(instance, k, v)
        return instance

    def _delete_internal(self, pk: Any, session: Session) -> None:
        instance = self._get_internal(pk, session)
        session.delete(instance)

    def _handle_integrity(self, exc: IntegrityError) -> None:
        msg = str(exc.orig)
        if m := _DUPLICATE_KEY_RE.search(msg):
            field, value = m.group("field"), m.group("value")
            raise DuplicateError(field_name=field, value=value) from exc

        if m := _CONSTRAINT_RE.search(msg):
            constraint = m.group("constraint")
            raise ConstraintViolationError(constraint_name=constraint) from exc

        raise TransactionError(msg) from exc  # fallback
