import logging
from contextlib import contextmanager
from functools import lru_cache, wraps
from typing import Callable, Generator, ParamSpec, TypeVar

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from config import settings

from .exceptions import StorageConfigurationError

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


@lru_cache(maxsize=1)
def create_storage_engine(*, url: str, echo: bool) -> Engine:
    logger.debug("Initializing database engine (url=%s, echo=%s)", url, echo)

    try:
        e = create_engine(url, echo=echo)
        logger.info("Database engine initialized")
        return e

    except Exception as exc:
        logger.critical(
            "Unexpected error during engine initialization: %s",
            exc,
            exc_info=True,
        )
        raise StorageConfigurationError(
            issue="Database engine initialization failed",
            component="engine_initialization",
            original_error=str(exc),
        ) from exc


def create_storage_session_factory(
    *,
    bind: Engine,
    autoflush: bool,
    autocommit: bool,
    expire_on_commit: bool,
) -> scoped_session:
    logger.debug(
        "Initializing session factory "
        "(autoflush=%s, autocommit=%s, expire_on_commit=%s)",
        autoflush,
        autocommit,
        expire_on_commit,
    )

    try:
        session_factory = scoped_session(
            sessionmaker(
                bind=bind,
                autoflush=autoflush,
                autocommit=autocommit,
                expire_on_commit=expire_on_commit,
            )
        )
        logger.info("Session factory initialized")
        return session_factory

    except Exception as exc:
        logger.critical(
            "Unexpected error during session factory initialization: %s",
            exc,
            exc_info=True,
        )
        raise StorageConfigurationError(
            issue="Session factory initialization failed",
            component="session_factory_initialization",
            original_error=str(exc),
        ) from exc


engine = create_storage_engine(
    url=str(settings.sqlalchemy.url),
    echo=settings.sqlalchemy.echo,
)

StorageSession = create_storage_session_factory(
    bind=engine,
    autoflush=settings.sqlalchemy.autoflush,
    autocommit=settings.sqlalchemy.autocommit,
    expire_on_commit=settings.sqlalchemy.expire_on_commit,
)


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session: Session = StorageSession()
    try:
        yield session
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error("Session rollback due to exception: %s", exc, exc_info=True)
        raise
    finally:
        session.close()


def inject_session(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        if kwargs.get("session") is None:
            with session_scope() as session:
                kwargs["session"] = session
                return func(*args, **kwargs)
        return func(*args, **kwargs)

    return wrapper
