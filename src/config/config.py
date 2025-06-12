from functools import lru_cache
from pathlib import Path
from typing import Sequence

from pydantic import BaseModel, PostgresDsn
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, TomlConfigSettingsSource

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_ROOT = PROJECT_ROOT / "config"

DEFAULT_REQUEST_TIMEOUT = 30
DEFAULT_POOL_CONNECTIONS = 100
DEFAULT_POOL_MAXSIZE = 30
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0
DEFAULT_MAX_RETRY_DELAY = 1.0

CONFIG_FILES = [
    CONFIG_ROOT / "config.toml",
    CONFIG_ROOT / "config.dev.toml",
]


class CrawlerConfig(BaseSettings):
    user_agents: Sequence[str] = []
    request_timeout: int = DEFAULT_REQUEST_TIMEOUT
    pool_connections: int = DEFAULT_POOL_CONNECTIONS
    pool_maxsize: int = DEFAULT_POOL_MAXSIZE
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_delay: float = DEFAULT_RETRY_DELAY
    max_retry_delay: float = DEFAULT_MAX_RETRY_DELAY


class DatabaseConfig(BaseModel):
    dsn: PostgresDsn


class Config(BaseSettings):
    model_config = SettingsConfigDict(toml_file=CONFIG_FILES)
    crawler: CrawlerConfig
    database: DatabaseConfig

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (TomlConfigSettingsSource(settings_cls),)


@lru_cache
def load() -> Config:
    return Config()  # noqa
