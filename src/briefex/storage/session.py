from __future__ import annotations

import logging
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from briefex.storage import StorageConfigurationError

_log = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")

engine: Engine | None = None
SessionFactory: sessionmaker[Session] | None = None


def init_connection(
    url: str,
    echo: bool,
    autoflush: bool,
    autocommit: bool,
    expire_on_commit: bool,
) -> None:
    """Initialize the global SQLAlchemy engine and session factory.

    Args:
        url: Database URL for the engine.
        echo: Flag to enable SQL statement logging.
        autoflush: Enable autoflush on session.
        autocommit: Enable autocommit on session.
        expire_on_commit: Expire objects on commit.

    Raises:
        StorageConfigurationError: If engine or session factory initialization fails.
    """
    global engine, SessionFactory

    _log.info(
        "Initializing database connection "
        "(url=%s, echo=%s, autoflush=%s, autocommit=%s, expire_on_commit=%s)",
        url,
        echo,
        autoflush,
        autocommit,
        expire_on_commit,
    )

    try:
        engine = create_engine(url, echo=echo)
    except Exception as exc:
        _log.error("Unexpected error during initialization engine: %s", exc)
        raise StorageConfigurationError(
            issue=f"Engine initialization failed: {exc}",
            stage="engine_initialization",
        ) from exc

    try:
        SessionFactory = sessionmaker(
            bind=engine,
            autoflush=autoflush,
            autocommit=autocommit,
            expire_on_commit=expire_on_commit,
        )
    except Exception as exc:
        _log.error("Unexpected error during initialization SessionFactory: %s", exc)
        raise StorageConfigurationError(
            issue=f"SessionFactory initialization failed: {exc}",
            stage="session_factory_initialization",
        ) from exc


def connect[P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Decorator that injects a Session and manages transaction scope.

    Args:
        func: Function to wrap; must accept a 'session' keyword argument.

    Returns:
        A wrapped function that provides session,
        commits on success, and rolls back on error.
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        """Execute the wrapped function within a session context.

        Returns:
            The result of the wrapped function.

        Raises:
            Exception: Propagates exceptions after rolling back the session.
        """
        with SessionFactory() as session:
            kwargs["session"] = session

            try:
                result: R = func(*args, **kwargs)
                session.commit()
                return result
            except Exception as exc:
                _log.error("Unexpected error during calling %s: %s", func.__name__, exc)
                session.rollback()
                raise

    return wrapper
