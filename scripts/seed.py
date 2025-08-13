from __future__ import annotations

import logging

from briefex.config import load_settings
from briefex.storage import (
    DuplicateObjectError,
    Source,
    SourceType,
    get_default_source_storage_factory,
    init_connection,
)

logging.basicConfig(level=logging.INFO)

_log = logging.getLogger(__name__)

DEFAULT_SOURCES: list[dict[str, str | SourceType]] = [
    {
        "name": "RT на русском",
        "code_name": "rt::html",
        "type": SourceType.HTML,
        "url": "https://russian.rt.com/news",
    }
]


def seed() -> None:
    """Insert default sources into the database if they do not exist."""
    settings = load_settings()
    init_connection(
        url=settings.sqlalchemy.sqlalchemy_url,
        echo=settings.sqlalchemy.echo,
        autoflush=settings.sqlalchemy.autoflush,
        expire_on_commit=settings.sqlalchemy.expire_on_commit,
    )

    storage = get_default_source_storage_factory().create()

    for data in DEFAULT_SOURCES:
        src = Source(**data)
        try:
            storage.add(src)
            _log.info("Seed source: '%s'", src.name)
        except DuplicateObjectError as exc:
            _log.error("Source already exists: '%s'", exc)


if __name__ == "__main__":
    seed()
