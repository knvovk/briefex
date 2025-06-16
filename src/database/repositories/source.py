import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..exceptions import ModelNotFoundError, map_sqlalchemy_error
from ..models import Source
from .base import BaseRepository, ensure_session
from .factory import register

logger = logging.getLogger(__name__)


@register(Source)
class SourceRepository(BaseRepository[Source]):

    def __init__(self) -> None:
        super().__init__(Source)

    @ensure_session
    def get_by_code_name(self, code_name: str, *, session: Session) -> Source:
        stmt = select(Source).filter_by(code_name=code_name)

        try:
            source: Source | None = session.scalars(stmt).one_or_none()
            if source is None:
                raise ModelNotFoundError(
                    name=self._model.__name__,
                    pk="unknown",
                    message=f"No Source object found with code_name: {code_name}",
                )

            logger.debug(
                "Found source '%s' (id=%s)",
                code_name,
                getattr(source, "id", "N/A"),
            )
            return source

        except Exception as exc:
            logger.exception("Unable to get Source by code_name '%s'", code_name)
            raise map_sqlalchemy_error(
                exc,
                details={
                    "operation": "get_by_code_name",
                    "model": self._model.__name__,
                    "code_name": code_name,
                },
            ) from exc
