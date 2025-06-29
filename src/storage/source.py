import logging

from .base import Storage
from .factory import register
from .models import Source

logger = logging.getLogger(__name__)


@register(Source)
class SourceStorage(Storage[Source]):

    def __init__(self) -> None:
        super().__init__(Source)
