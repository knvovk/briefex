from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class SourceType(str, Enum):
    HTML = "HTML"
    RSS = "RSS"


class Source(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    code_name: str
    type: SourceType
    url: str

    def __repr__(self) -> str:
        return f"{self.name} (code_name={self.code_name}, type={self.type})"

    def __str__(self) -> str:
        return repr(self)


class Post(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    content: str
    url: str
    pub_date: datetime
    source: Source


class PostDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    title: str | None = None
    content: str | None = None
    url: str | None = None
    pub_date: datetime | None = None
    source: Source | None = None

    def merge(self, other: PostDraft) -> None:
        if not isinstance(other, PostDraft):
            raise TypeError(f"Expected PostDraft, got {type(other).__name__} instead")

        for field_name in self.model_fields:
            other_value = getattr(other, field_name)
            if other_value is not None:
                setattr(self, field_name, other_value)

    @classmethod
    def to_post(cls, draft: PostDraft) -> Post:
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
