import logging

from .base import Storage
from .models import Source
from .registry import register

logger = logging.getLogger(__name__)


@register(Source)
class SourceStorage(Storage[Source]):

    def __init__(self) -> None:
        super().__init__(Source)
