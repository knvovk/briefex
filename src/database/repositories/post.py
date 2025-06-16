import logging
from datetime import datetime, timedelta, timezone
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..exceptions import map_sqlalchemy_error
from ..models import Post
from .base import BaseRepository, ensure_session
from .factory import register

logger = logging.getLogger(__name__)

DEFAULT_RECENT_DAYS = 7


@register(Post)
class PostRepository(BaseRepository[Post]):

    def __init__(self) -> None:
        super().__init__(Post)

    @ensure_session
    def list_recent(
        self,
        days: int = DEFAULT_RECENT_DAYS,
        *,
        session: Session,
    ) -> Sequence[Post]:
        cutoff: datetime = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(Post)
            .where(Post.published_at >= cutoff)
            .order_by(Post.published_at.desc())
        )

        try:
            posts: list[Post] = list(session.scalars(stmt).all())
            logger.info("Loaded %d posts newer than %s", len(posts), cutoff.date())
            return posts
        except Exception as exc:
            logger.exception("Unable to load recent posts")
            raise map_sqlalchemy_error(
                exc,
                details={
                    "operation": "list_recent",
                    "model": self._model.__name__,
                    "days": days,
                },
            ) from exc
