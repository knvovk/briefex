import logging
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import lru_cache, wraps
from typing import ParamSpec, TypeVar

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from briefex import config

from .exceptions import StorageConfigurationError

logger = logging.getLogger(__name__)

settings = config.load_settings()

P = ParamSpec("P")
R = TypeVar("R")


@lru_cache(maxsize=1)
def create_storage_engine(*, url: str, echo: bool) -> Engine:
    """Create an SQLAlchemy engine for database connections.

    This function creates and returns an SQLAlchemy engine configured with the
    given URL and echo setting.
    The result is cached, so later calls with the same arguments return
    the same engine instance.

    Args:
        url: The database connection URL.
        echo: Whether to echo SQL statements to the console.

    Returns:
        A configured SQLAlchemy engine.

    Raises:
        StorageConfigurationError: If engine initialization fails.
    """
    logger.debug("Initializing database engine (url=%s, echo=%s)", url, echo)

    try:
        e = create_engine(url, echo=echo)
        logger.info("Database engine initialized")
        return e

    except Exception as exc:
        logger.critical("Unexpected error during engine initialization: %s", exc)
        raise StorageConfigurationError(
            issue="Database engine initialization failed",
            component="engine_initialization",
        ) from exc


def create_storage_session_factory(
    *,
    bind: Engine,
    autoflush: bool,
    autocommit: bool,
    expire_on_commit: bool,
) -> scoped_session:
    """Create a scoped session factory for database sessions.

    This function creates and returns an SQLAlchemy scoped session factory
    configured with the given parameters.

    Args:
        bind: The engine to bind the session to.
        autoflush: Whether to automatically flush the session.
        autocommit: Whether to automatically commit the session.
        expire_on_commit: Whether to expire objects after commit.

    Returns:
        A configured SQLAlchemy scoped session factory.

    Raises:
        StorageConfigurationError: If session factory initialization fails.
    """
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
        )
        raise StorageConfigurationError(
            issue="Session factory initialization failed",
            component="session_factory_initialization",
        ) from exc


# Global SQLAlchemy engine instance for database connections
engine = create_storage_engine(
    url=str(settings.sqlalchemy.url),
    echo=settings.sqlalchemy.echo,
)

# Global scoped session factory for creating database sessions
StorageSession = create_storage_session_factory(
    bind=engine,
    autoflush=settings.sqlalchemy.autoflush,
    autocommit=settings.sqlalchemy.autocommit,
    expire_on_commit=settings.sqlalchemy.expire_on_commit,
)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Context manager for handling database sessions.

    This context manager creates a new session, yields it, and handles committing or
    rolling back the transaction based on whether an exception occurs.

    Yields:
        A SQLAlchemy session.

    Raises:
        Any exception that occurs during the session's lifetime.
    """
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


def inject_session(func: Callable[P, R]) -> Callable[P, R]:  # noqa: UP047
    """Decorator for injecting a database session into a function.

    This decorator checks if a session is provided in the function's keyword arguments.
    If not, it creates a new session using session_scope and injects it.

    Args:
        func: The function to decorate.

    Returns:
        The decorated function.

    Example:
        @inject_session
        def get_user(user_id: int, *, session: Session) -> User:
            return session.query(User).get(user_id)
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        if kwargs.get("session") is None:
            with session_scope() as session:
                kwargs["session"] = session
                return func(*args, **kwargs)
        return func(*args, **kwargs)

    return wrapper
