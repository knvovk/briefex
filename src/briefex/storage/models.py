from __future__ import annotations

import datetime as dt
import enum
import uuid

from sqlalchemy import Enum as PgEnum
from sqlalchemy import ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Model(DeclarativeBase):
    """Abstract base class for all declarative ORM models."""

    __abstract__ = True


class SourceType(str, enum.Enum):
    """Supported content source types."""

    HTML = "HTML"
    RSS = "RSS"


class Source(Model):
    """Represents a content source with its metadata and relationships."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    code_name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    type: Mapped[SourceType] = mapped_column(
        PgEnum(SourceType, name="source_type_enum", native_enum=True),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    posts: Mapped[list[Post]] = relationship(back_populates="source")

    __tablename__ = "sources"

    def __repr__(self) -> str:
        return f"{self.name} (code_name={self.code_name}, type={self.type})"


class PostStatus(enum.IntEnum):
    """Enumeration of possible post processing states."""

    PENDING_SUMMARY = 10

    SUMMARY_READY = 20
    SUMMARY_RETRY = 25
    SUMMARY_CENSORED = 30

    MODERATION_APPROVED = 40
    MODERATION_REJECTED = 45

    SCHEDULED = 50
    PUBLISHED = 60

    ARCHIVED = 90


class Post(Model):
    """Represents a crawled post with content, status, and metadata."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(String, nullable=True)
    canonical_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        unique=True,
    )
    status: Mapped[PostStatus] = mapped_column(
        PgEnum(PostStatus, name="post_status_enum", native_enum=True),
        nullable=False,
        index=True,
        default=PostStatus.PENDING_SUMMARY,
        server_default=text(f"'{PostStatus.PENDING_SUMMARY.name}'"),
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    published_at: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    source: Mapped[Source] = relationship(back_populates="posts")

    __tablename__ = "posts"

    def __repr__(self) -> str:
        return f"Post(id={self.id})"

    def __str__(self) -> str:
        return repr(self)
