from __future__ import annotations

import datetime as dt
import enum
import uuid

from sqlalchemy import Enum as PgEnum
from sqlalchemy import ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Model(DeclarativeBase):
    """Base model class for all database models.

    This is an abstract base class that all model classes should inherit from.
    It provides common functionality for all models.
    """

    __abstract__ = True


class SourceType(str, enum.Enum):
    """Enumeration of supported source types.

    This enum defines the types of sources that can be crawled.

    Attributes:
        HTML: HTML web page source type.
        RSS: RSS feed source type.
    """

    HTML = "HTML"
    RSS = "RSS"


class Source(Model):
    """Model representing a content source.

    A source is a website or feed from which posts are collected.

    Attributes:
        id: Unique identifier for the source.
        name: Human-readable name of the source.
        code_name: Machine-readable unique identifier for the source.
        type: Type of the source (HTML or RSS).
        url: URL of the source.
        created_at: Timestamp when the source was created.
        updated_at: Timestamp when the source was last updated.
        posts: List of posts from this source.
    """

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
        """Return a string representation of the Source object.

        Returns:
            A string containing the code_name and type of the source.
        """
        return f"{self.name} (code_name={self.code_name}, type={self.type})"


class PostStatus(enum.IntEnum):
    """Enumeration of post statuses.

    This enum defines the possible statuses of a post.

    Attributes:
        PENDING_SUMMARY: Post is pending summary generation.
        SUMMARY_READY: Summary generation is complete and ready for moderation.
        SUMMARY_RETRY: Summary generation failed and needs to be retried.
        SUMMARY_CENSORED: Summary generation was censored and should not be published.
        MODERATION_APPROVED: Post has been approved for publication.
        MODERATION_REJECTED: Post has been rejected for publication.
        SCHEDULED: Post is scheduled for publication.
        PUBLISHED: Post has been published.
        ARCHIVED: Post has been archived and is no longer available.
    """

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
    """Model representing a content post.

    A post is a piece of content collected from a source.

    Attributes:
        id: Unique identifier for the post.
        title: Title of the post.
        content: Full content of the post.
        summary: Brief summary of the post content.
        canonical_url: Original URL of the post.
        source_id: ID of the source this post was collected from.
        published_at: Timestamp when the post was published.
        created_at: Timestamp when the post was created in the system.
        updated_at: Timestamp when the post was last updated.
        source: The source this post was collected from.
    """

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
        """Return a string representation of the Post object.

        Returns:
            A string containing the title and source of the post.
        """
        return f"Post(id={self.id})"

    def __str__(self) -> str:
        """Return a string representation of the Post object.

        Returns:
            A string containing the title and source of the post.
        """
        return repr(self)
