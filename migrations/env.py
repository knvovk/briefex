from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

project_root = Path(__file__).resolve().parents[1]
src_root = project_root / "src"
sys.path.append(src_root.as_posix())

from src.config import load as load_app_config
from src.storage import models

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

app_config = load_app_config()
config.set_main_option("sqlalchemy.url", str(app_config.database.url))

target_metadata = models.Model.metadata


def _configure_alembic(**kwargs) -> None:
    context.configure(
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        **kwargs,
    )


def run_migrations_offline() -> None:
    _configure_alembic(
        url=config.get_main_option("sqlalchemy.url"),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        _configure_alembic(connection=connection)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
