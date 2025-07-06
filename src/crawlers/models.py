from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class SourceType(str, Enum):
    """Enumeration of supported source types.

    This enum defines the types of sources that can be crawled.

    Attributes:
        HTML: HTML source type.
        RSS: RSS source type.
    """

    HTML = "HTML"
    RSS = "RSS"


class Source(BaseModel):
    """Model representing a source to crawl.

    A source is a website or feed that can be crawled to extract posts.

    Attributes:
        name: The display name of the source.
        code_name: The unique code name of the source.
        type: The type of the source (HTML or RSS).
        url: The URL of the source.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    code_name: str
    type: SourceType
    url: str

    def __repr__(self) -> str:
        """Get a string representation of the source.

        Returns:
            A string representation of the source.
        """
        return f"{self.name} (code_name={self.code_name}, type={self.type})"

    def __str__(self) -> str:
        """Get a string representation of the source.

        Returns:
            A string representation of the source.
        """
        return repr(self)


class Post(BaseModel):
    """Model representing a post extracted from a source.

    A post is a complete article or entry extracted from a source.

    Attributes:
        id: The unique identifier of the post.
        title: The title of the post.
        content: The content of the post.
        url: The URL of the post.
        pub_date: The publication date of the post.
        source: The source the post was extracted from.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    content: str
    url: str
    pub_date: datetime
    source: Source


class PostDraft(BaseModel):
    """Model representing a draft of a post.

    A post-draft is an incomplete post that is being built during the crawling process.
    Fields can be None until they are populated.

    Attributes:
        id: The unique identifier of the post, or None.
        title: The title of the post, or None.
        content: The content of the post, or None.
        url: The URL of the post, or None.
        pub_date: The publication date of the post, or None.
        source: The source the post was extracted from, or None.
    """

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    title: str | None = None
    content: str | None = None
    url: str | None = None
    pub_date: datetime | None = None
    source: Source | None = None

    def merge(self, other: PostDraft) -> None:
        """Merge another PostDraft into this one.

        Non-None fields from the other draft will overwrite fields in this draft.

        Args:
            other: The other PostDraft to merge from.

        Raises:
            TypeError: If other is not a PostDraft.
        """
        if not isinstance(other, PostDraft):
            raise TypeError(f"Expected PostDraft, got {type(other).__name__} instead")

        for field_name in self.model_fields:
            other_value = getattr(other, field_name)
            if other_value is not None:
                setattr(self, field_name, other_value)

    @classmethod
    def to_post(cls, draft: PostDraft) -> Post:
        """Convert a PostDraft to a Post.

        This method checks that all required fields are present and creates a Post.

        Args:
            draft: The PostDraft to convert.

        Returns:
            A Post created from the draft.

        Raises:
            ValueError: If any required fields are missing.
        """
        required_fields = ["id", "title", "content", "url", "pub_date", "source"]
        missing_fields = [
            field for field in required_fields if getattr(draft, field) is None
        ]

        if missing_fields:
            raise ValueError(f"Missing required fields in PostDraft: {missing_fields}")

        return Post(
            id=draft.id,
            title=draft.title,
            content=draft.content,
            url=draft.url,
            pub_date=draft.pub_date,
            source=draft.source,
        )
