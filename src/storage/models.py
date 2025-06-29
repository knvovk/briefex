from __future__ import annotations

import datetime as dt
import enum
import uuid

from sqlalchemy import Enum as PgEnum
from sqlalchemy import ForeignKey, String, func
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Model(DeclarativeBase):
    __abstract__ = True


class SourceType(str, enum.Enum):
    HTML = "HTML"
    RSS = "RSS"


class Source(Model):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    code_name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    type: Mapped[SourceType] = mapped_column(
        PgEnum(SourceType, name="source_type_enum"),
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
        return f"Source(code_name={self.code_name!r}, type={self.type!r})"


class Post(Model):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(String, nullable=False)
    canonical_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        unique=True,
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
        return f"Post(title={self.title!r}, source={self.source!r})"
