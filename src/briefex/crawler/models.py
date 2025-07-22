from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel

SourceType = Literal["HTML", "RSS"]
type SourceCode = str

TIME_1970_01_01 = datetime(1970, 1, 1, 0, 0, 0, tzinfo=UTC)


class Source(BaseModel):
    name: str
    code: str
    type: SourceType
    url: SourceCode
    encoding: str
    article_tag: str
    article_cls: str
    post_card_tag: str
    post_card_cls: str
    datetime_fmt: str

    @property
    def article_selector(self) -> str:
        return f"{self.article_tag}.{self.article_cls}"

    @property
    def card_selector(self) -> str:
        return f"{self.card_tag}.{self.card_cls}"


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
