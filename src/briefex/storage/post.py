import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .base import Storage
from .models import Post
from .registry import register
from .session import inject_session

logger = logging.getLogger(__name__)


@register(Post)
class PostStorage(Storage[Post]):
    """Storage class for Post model.

    This class provides methods for storing and retrieving Post objects.
    It extends the base Storage class with Post-specific functionality.
    """

    def __init__(self) -> None:
        """Initialize a new PostStorage instance.

        Sets up the storage with the Post model.
        """
        super().__init__(Post)

    @inject_session
    def get_recent(self, days: int, *, session: Session) -> list[Post]:
        """Retrieve posts published within the specified number of days.

        Args:
            days: Number of days to look back.
            session: The database session to use.

        Returns:
            A list of Post objects published within the specified time period,
            ordered by publication date (newest first).

        Raises:
            StorageException: If there's an error during the operation.
        """
        return self._execute(lambda: self._get_recent_func(days, session))

    def _get_recent_func(self, days: int, session: Session) -> list[Post]:
        """Internal method to retrieve recent posts.

        This method implements the actual database query to retrieve posts
        published within the specified number of days.

        Args:
            days: Number of days to look back.
            session: The database session to use.

        Returns:
            A list of Post objects published within the specified time period,
            ordered by publication date (newest first).
        """
        logger.debug("Retrieving recent Post objects")

        cutoff = datetime.now(UTC) - timedelta(days=days)
        query = (
            select(self._model)
            .where(self._model.created_at >= cutoff)
            .order_by(self._model.created_at.desc())
        )
        objs = list(session.scalars(query).all())

        logger.debug("%d recent Post objects retrieved", len(objs))
        return objs
