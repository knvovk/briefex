from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel

SourceType = Literal["HTML", "RSS"]
type SourceCode = str

TIME_1970_01_01 = datetime(1970, 1, 1, 0, 0, 0, tzinfo=UTC)


class Source(BaseModel):
    """Model representing a source to crawl."""

    name: str
    code: str
    type: SourceType
    url: SourceCode


class Post(BaseModel):
    """Model for a fully parsed post."""

    title: str
    content: str
    canonical_url: str
    published_at: datetime
    source: Source


class PostDraft(BaseModel):
    """Model for intermediate post draft with optional fields."""

    title: str | None = None
    content: str | None = None
    canonical_url: str | None = None
    published_at: datetime | None = None
    source: Source | None = None

    def merge(self, other: PostDraft) -> None:
        """Merge non-null fields from another draft into this one.

        Args:
            other: Draft whose non-null fields override this draft's fields.
        """
        for field_name in PostDraft.model_fields():
            other_value = getattr(other, field_name)
            if other_value is not None:
                setattr(self, field_name, other_value)

    def to_post(self) -> Post:
        """Convert a complete draft to a Post, ensuring all fields are present.

        Returns:
            A Post instance with all required fields populated.

        Raises:
            ValueError: If any required field is missing.
        """
        required_fields = (
            "title",
            "content",
            "canonical_url",
            "published_at",
            "source",
        )
        missing_fields = [f for f in required_fields if getattr(self, f) is None]
        if missing_fields:
            raise ValueError(f"Missing required fields in PostDraft: {missing_fields}")

        return Post(
            title=self.title,
            content=self.content,
            canonical_url=self.canonical_url,
            published_at=self.published_at,
            source=self.source,
        )
