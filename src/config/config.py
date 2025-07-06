from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
"""Path to the base directory of the config module."""

ENV_PATH = BASE_DIR / ".env"
"""Path to the environment file."""


class CrawlerConfig(BaseModel):
    """Configuration for web crawler settings.

    This class defines parameters for HTTP requests, connection pooling,
    and retry behavior for the web crawler component.

    Attributes:
        req_timeout: Request timeout in seconds.
        pool_conn: Connection pool size.
        pool_max_size: Maximum pool size.
        max_retries: Maximum number of retry attempts.
        retry_delay: Initial delay between retries in seconds.
        max_retry_delay: Maximum delay between retries in seconds.
    """

    req_timeout: int = Field(description="Request timeout in seconds")
    pool_conn: int = Field(description="Connection pool size")
    pool_max_size: int = Field(description="Maximum pool size")
    max_retries: int = Field(description="Maximum number of retry attempts")
    retry_delay: float = Field(description="Initial delay between retries in seconds")
    max_retry_delay: float = Field(
        description="Maximum delay between retries in seconds"
    )


class LLMConfig(BaseModel):
    """Configuration for Large Language Model (LLM) settings.

    This class defines parameters for different LLM providers (GigaChat, YandexGPT)
    and general LLM settings for text completion.

    Attributes:
        giga_chat_client_id: GigaChat client ID.
        giga_chat_client_secret: GigaChat client secret.
        giga_chat_auth_key: GigaChat authentication key.
        giga_chat_scope: GigaChat API scope.
        yandex_gpt_folder_id: YandexGPT folder ID.
        yandex_gpt_api_key: YandexGPT API key.
        completion_model: Default completion model to use.
        completion_temperature: Model temperature parameter.
        completion_max_tokens: Maximum tokens for completion.
    """

    # GigaChat settings
    giga_chat_client_id: str = Field(description="GigaChat client ID")
    giga_chat_client_secret: str = Field(description="GigaChat client secret")
    giga_chat_auth_key: str = Field(description="GigaChat authentication key")
    giga_chat_scope: str = Field(description="GigaChat API scope")

    # YandexGPT settings
    yandex_gpt_folder_id: str = Field(description="YandexGPT folder ID")
    yandex_gpt_api_key: str = Field(description="YandexGPT API key")

    # General LLM settings
    completion_model: str = Field(description="Default completion model to use")
    completion_temperature: float = Field(description="Model temperature parameter")
    completion_max_tokens: int = Field(description="Maximum tokens for completion")


class SQLAlchemyConfig(BaseModel):
    """Configuration for SQLAlchemy database settings.

    This class defines connection parameters and behavior settings
    for the SQLAlchemy ORM.

    Attributes:
        url: Database connection URL.
        echo: Enable SQL query logging.
        autoflush: Enable autoflush.
        autocommit: Enable autocommit.
        expire_on_commit: Expire objects on commit.
    """

    url: PostgresDsn = Field(description="Database connection URL")
    echo: bool = Field(description="Enable SQL query logging")
    autoflush: bool = Field(description="Enable autoflush")
    autocommit: bool = Field(description="Enable autocommit")
    expire_on_commit: bool = Field(description="Expire objects on commit")


class Settings(BaseSettings):
    """Main application settings class.

    This class combines all configuration components and handles
    loading settings from environment variables and .env files.

    Attributes:
        crawler: Configuration for web crawler settings.
        llm: Configuration for Language Learning Model settings.
        sqlalchemy: Configuration for SQLAlchemy database settings.
        model_config: Pydantic configuration for settings behavior.
    """

    crawler: CrawlerConfig = Field(default_factory=CrawlerConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    sqlalchemy: SQLAlchemyConfig = Field(default_factory=SQLAlchemyConfig)

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        env_nested_max_split=1,
        extra="ignore",
    )


settings = Settings()
"""Global settings instance for the application."""
