from datetime import datetime
from typing import Literal

from pydantic import BaseModel

SourceType = Literal["HTML", "RSS"]
type SourceCode = str


class Source(BaseModel):
    name: str
    code: str
    type: SourceType
    url: SourceCode


class Post(BaseModel):
    title: str
    content: str
    canonical_url: str
    published_at: datetime
    source: Source


class PostDraft(BaseModel):
    title: str | None = None
    content: str | None = None
    canonical_url: str | None = None
    published_at: datetime | None = None
    source: Source | None = None
