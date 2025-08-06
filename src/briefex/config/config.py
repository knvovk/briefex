from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, PostgresDsn, RedisDsn
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
    lookback_days: int = Field(description="Recent post days")


class IntelligenceConfig(BaseModel):
    """Configuration for intelligence settings.

    This class defines parameters for various intelligence components.

    Attributes:
        summarization_prompt: Summarization prompt.
        summarization_model: Summarization model.
        summarization_max_tokens: Summarization max tokens.
        summarization_temperature: Summarization temperature.
        summarization_top_p: Summarization top p.
        summarization_top_k: Summarization top k.
    """

    summarization_prompt: str = Field(description="Summarization prompt")
    summarization_model: str = Field(description="Summarization model")
    summarization_max_tokens: int = Field(description="Summarization max tokens")
    summarization_temperature: float = Field(description="Summarization temperature")
    summarization_top_p: float = Field(description="Summarization top p")
    summarization_top_k: int = Field(description="Summarization top k")


class LLMConfig(BaseModel):
    """Configuration for Large Language Model (LLM) settings.

    This class defines parameters for different LLM providers (GigaChat, YandexGPT)
    and general LLM settings for text completion.

    Attributes:
        gigachat_client_id: GigaChat client ID.
        gigachat_client_secret: GigaChat client secret.
        gigachat_auth_key: GigaChat authentication key.
        gigachat_model: GigaChat default model.
        gigachat_scope: GigaChat API scope.
        gigachat_verify_ssl_certs: Enable SSL certificate verification.

        yandex_gpt_folder_id: YandexGPT folder ID.
        yandex_gpt_api_key: YandexGPT API key.
    """

    # GigaChat settings
    gigachat_client_id: str = Field(description="GigaChat client ID")
    gigachat_client_secret: str = Field(description="GigaChat client secret")
    gigachat_auth_key: str = Field(description="GigaChat authentication key")
    gigachat_model: str = Field(description="GigaChat default model")
    gigachat_scope: str = Field(description="GigaChat API scope")
    gigachat_verify_ssl_certs: bool = Field(description="GigaChat verify SSL certs")

    # YandexGPT settings
    yandex_gpt_folder_id: str = Field(description="YandexGPT folder ID")
    yandex_gpt_api_key: str = Field(description="YandexGPT API key")


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


class CeleryConfig(BaseModel):
    """Configuration for Celery task queue settings."""

    broker_url: RedisDsn = Field(description="Broker URL")
    result_backend: RedisDsn = Field(description="Result backend URL")
    task_serializer: str = Field(description="Task serializer")
    result_serializer: str = Field(description="Result serializer")
    accept_content: list[str] = Field(description="Accept content")
    timezone: str = Field(description="Timezone")
    enable_utc: bool = Field(description="Enable UTC")
    hijack_root_logger: bool = Field(description="Hijack root logger")


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
    intelligence: IntelligenceConfig = Field(default_factory=IntelligenceConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    sqlalchemy: SQLAlchemyConfig = Field(default_factory=SQLAlchemyConfig)
    celery: CeleryConfig = Field(default_factory=CeleryConfig)

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        env_nested_max_split=1,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    """Load application settings from environment variables and .env file.

    This function initializes the global settings instance and returns it.

    Returns:
        Settings: The initialized settings instance.
    """
    return Settings()
