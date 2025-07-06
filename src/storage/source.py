import logging

from .base import Storage
from .models import Source
from .registry import register

logger = logging.getLogger(__name__)


@register(Source)
class SourceStorage(Storage[Source]):
    """Storage class for Source model.

    This class provides methods for storing and retrieving Source objects.
    It extends the base Storage class with Source-specific functionality.
    """

    def __init__(self) -> None:
        """Initialize a new SourceStorage instance.

        Sets up the storage with the Source model.
        """
        super().__init__(Source)
