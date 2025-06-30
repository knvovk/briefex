import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .base import Storage
from .models import Post
from .registry import register
from .session import inject_session

logger = logging.getLogger(__name__)


@register(Post)
class PostStorage(Storage[Post]):

    def __init__(self) -> None:
        super().__init__(Post)

    @inject_session
    def get_recent(self, days: int, *, session: Session) -> list[Post]:
        return self._execute(lambda: self._get_recent_func(days, session))

    def _get_recent_func(self, days: int, session: Session) -> list[Post]:
        logger.debug("Retrieving recent Post objects")

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        query = (
            select(self._model)
            .where(self._model.published_at >= cutoff)
            .order_by(self._model.published_at.desc())
        )
        objs = list(session.scalars(query).all())

        logger.debug("%d recent Post objects retrieved", len(objs))
        return objs
