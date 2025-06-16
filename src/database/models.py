from __future__ import annotations

import datetime as dt
import enum
import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger
from sqlalchemy import Enum as PgEnum
from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

SOURCE_NAME_MAX_LENGTH = 256
SOURCE_CODE_NAME_MAX_LENGTH = 64
URL_MAX_LENGTH = 2048
POST_TITLE_MAX_LENGTH = 512
EMBEDDING_VECTOR_SIZE = 768


class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    created_at: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SourceType(str, enum.Enum):
    HTML = "HTML"
    RSS = "RSS"


class Source(Base, UUIDMixin, TimestampMixin):
    name: Mapped[str] = mapped_column(String(SOURCE_NAME_MAX_LENGTH), nullable=False)
    code_name: Mapped[str] = mapped_column(
        String(SOURCE_CODE_NAME_MAX_LENGTH),
        nullable=False,
        unique=True,
    )
    type: Mapped[SourceType] = mapped_column(
        PgEnum(SourceType, name="source_type_enum"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(String(URL_MAX_LENGTH), nullable=False)

    posts: Mapped[list[Post]] = relationship(back_populates="source")

    __tablename__ = "sources"
    __table_args__ = (
        UniqueConstraint("url", name="uq_sources_url"),
        Index("ix_sources_code_name_lower", code_name.desc()),
    )

    def __repr__(self) -> str:
        return f"<Source {self.code_name!r} ({self.type})>"


class Post(Base, UUIDMixin, TimestampMixin):
    title: Mapped[str] = mapped_column(String(POST_TITLE_MAX_LENGTH), nullable=False)
    canonical_url: Mapped[str] = mapped_column(
        String(URL_MAX_LENGTH),
        nullable=False,
        unique=True,
    )
    summary: Mapped[str] = mapped_column(String, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_VECTOR_SIZE))
    text_hash: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        unique=True,
        index=True,
    )
    published_at: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    source: Mapped[Source] = relationship(back_populates="posts")

    __tablename__ = "posts"
    __table_args__ = (
        Index("ix_posts_embedding", "embedding", postgresql_using="ivfflat"),
    )

    def __repr__(self) -> str:
        return f"<Post {self.title!r} ({self.canonical_url})>"
