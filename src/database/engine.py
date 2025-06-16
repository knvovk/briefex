import logging
from functools import lru_cache

from sqlalchemy import Engine, create_engine

import config

from .exceptions import DatabaseConfigurationError

__all__ = ["engine", "create_db_engine"]

logger = logging.getLogger(__name__)

_db_cfg = config.load().database


@lru_cache(maxsize=1)
def create_db_engine(*, url: str, echo: bool) -> Engine:
    logger.debug("Creating database engine (url=%s, echo=%s)", url, echo)

    try:
        engine = create_engine(url, echo=echo)
        logger.info("Database engine successfully initialized")
        return engine

    except Exception as exc:
        logger.critical(
            "Unexpected error during engine initialization: %s",
            exc,
            exc_info=True,
        )
        raise DatabaseConfigurationError(
            issue="Database engine initialization failed",
            component="engine_initialization",
            original_error=str(exc),
        ) from exc


engine = create_db_engine(url=str(_db_cfg.url), echo=_db_cfg.echo)
