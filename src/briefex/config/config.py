from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import ClassVar
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, RedisDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"


class CrawlerConfig(BaseModel):
    """HTTP crawler runtime configuration."""

    req_timeout: int = Field(
        default=15,
        ge=1,
        description="Request timeout in seconds",
    )
    pool_conn: int = Field(
        default=10,
        ge=1,
        description="Connection pool size",
    )
    pool_max_size: int = Field(
        default=50,
        ge=1,
        description="Maximum pool size",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum number of retry attempts",
    )
    retry_delay: float = Field(
        default=0.5,
        ge=0.0,
        description="Initial delay between retries in seconds",
    )
    max_retry_delay: float = Field(
        default=8.0,
        ge=0.0,
        description="Maximum delay between retries in seconds",
    )
    lookback_days: int = Field(
        default=3,
        ge=0,
        description="Recent post days",
    )


class IntelligenceConfig(BaseModel):
    """Parameters for the summarization pipeline."""

    summarization_prompt: str = Field(
        default="Summarize the text.",
        description="Summarization prompt",
    )
    summarization_model: str = Field(
        default="yandexgpt",
        description="Summarization model",
    )
    summarization_max_tokens: int = Field(
        default=512,
        ge=1,
        description="Summarization max tokens",
    )
    summarization_temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="Summarization temperature",
    )
    summarization_top_p: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Summarization top p",
    )
    summarization_top_k: int = Field(
        default=50,
        ge=1,
        description="Summarization top k",
    )


class LLMConfig(BaseModel):
    """Credentials and defaults for LLM providers."""

    gigachat_client_id: str = Field(
        default="",
        description="GigaChat client ID",
    )
    gigachat_client_secret: SecretStr = Field(
        default=SecretStr(""),
        description="GigaChat client secret",
    )
    gigachat_auth_key: SecretStr = Field(
        default=SecretStr(""),
        description="GigaChat authentication key",
    )
    gigachat_model: str = Field(
        default="lite",
        description="GigaChat default model",
    )
    gigachat_scope: str = Field(
        default="GIGACHAT_API_PERS",
        description="GigaChat API scope",
    )
    gigachat_verify_ssl_certs: bool = Field(
        default=True,
        description="GigaChat verify SSL certs",
    )

    yandex_gpt_folder_id: str = Field(
        default="",
        description="YandexGPT folder ID",
    )
    yandex_gpt_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="YandexGPT API key",
    )


class SQLAlchemyConfig(BaseModel):
    """Database connection settings and helpers."""

    ALLOWED_SCHEMES: ClassVar[frozenset[str]] = frozenset(
        {"postgres", "postgresql", "postgresql+psycopg"}
    )

    url: str = Field(description="Database connection URL")
    echo: bool = Field(default=False, description="Enable SQL query logging")
    autoflush: bool = Field(default=True, description="Enable autoflush")
    expire_on_commit: bool = Field(default=True, description="Expire objects on commit")

    @field_validator("url", mode="before")
    @classmethod
    def _validate_db_url(cls, v: object) -> str:
        raw = str(v)
        scheme = urlsplit(raw).scheme.lower()
        if scheme not in cls.ALLOWED_SCHEMES:
            allowed = ", ".join(sorted(cls.ALLOWED_SCHEMES))
            raise ValueError(
                f"Invalid DB URL scheme '{scheme}'. Allowed schemes: {allowed}"
            )
        return raw

    @property
    def sqlalchemy_url(self) -> str:
        """Return SQLAlchemy-compatible URL, normalizing postgres schemes."""
        raw = str(self.url)
        lower = raw.lower()

        if lower.startswith("postgres://"):
            return "postgresql+psycopg://" + raw[len("postgres://") :]
        if lower.startswith("postgresql://") and not lower.startswith("postgresql+"):
            return "postgresql+psycopg://" + raw[len("postgresql://") :]
        return raw


class CeleryConfig(BaseModel):
    """Celery broker/backend and serialization settings."""

    broker_url: RedisDsn = Field(description="Broker URL")
    result_backend: RedisDsn = Field(description="Result backend URL")
    task_serializer: str = Field(default="json", description="Task serializer")
    result_serializer: str = Field(default="json", description="Result serializer")
    accept_content: list[str] = Field(
        default_factory=lambda: ["json"],
        description="Accept content",
    )
    timezone: str = Field(default="UTC", description="Timezone")
    enable_utc: bool = Field(default=True, description="Enable UTC")
    worker_hijack_root_logger: bool = Field(
        default=False,
        description="Hijack root logger",
    )


class Settings(BaseSettings):
    """Aggregated application settings loaded from environment and .env."""

    crawler: CrawlerConfig = Field(default_factory=CrawlerConfig)
    intelligence: IntelligenceConfig = Field(default_factory=IntelligenceConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    sqlalchemy: SQLAlchemyConfig = Field(default_factory=SQLAlchemyConfig)
    celery: CeleryConfig = Field(default_factory=CeleryConfig)

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_prefix="BRIEFEX_",
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    """Load and cache application settings."""
    return Settings()
