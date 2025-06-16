import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

import config

from .engine import engine
from .exceptions import DatabaseConfigurationError

__all__ = ["SessionLocal", "session_scope"]

logger = logging.getLogger(__name__)

_db_cfg = config.load().database


def _create_session_factory(
    *,
    bind: Engine,
    autoflush: bool,
    autocommit: bool,
    expire_on_commit: bool,
) -> scoped_session:
    logger.debug(
        "Creating session factory (autoflush=%s, autocommit=%s, expire_on_commit=%s)",
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
        logger.info("Session factory successfully created")
        return session_factory

    except Exception as exc:
        logger.critical(
            "Unexpected error during session factory initialization: %s",
            exc,
            exc_info=True,
        )
        raise DatabaseConfigurationError(
            issue="Session factory initialization failed",
            component="session_factory_initialization",
            original_error=str(exc),
        ) from exc


SessionLocal = _create_session_factory(
    bind=engine,
    autoflush=_db_cfg.autoflush,
    autocommit=_db_cfg.autocommit,
    expire_on_commit=_db_cfg.expire_on_commit,
)


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error("Session rollback due to exception: %s", exc, exc_info=True)
        raise
    finally:
        session.close()
