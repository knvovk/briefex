import logging

import crawlers
import storage

logger = logging.getLogger(__name__)


class SourceMapper:
    """Utility class for mapping between different Source representations.

    This class provides static methods to convert between crawler Source objects
    and storage Source objects, ensuring data consistency across different
    modules of the application.
    """

    @staticmethod
    def from_crawlers_to_storage(src: crawlers.Source) -> storage.Source:
        """Convert a crawler Source object to a storage Source object.

        Args:
            src: The crawler Source object to convert.

        Returns:
            A storage Source object with equivalent data.
        """
        return storage.Source(
            name=src.name,
            code_name=src.code_name,
            type=storage.SourceType(src.type.value),
            url=src.url,
        )

    @staticmethod
    def from_storage_to_crawlers(src: storage.Source) -> crawlers.Source:
        """Convert a storage Source object to a crawler Source object.

        Args:
            src: The storage Source object to convert.

        Returns:
            A crawler Source object with equivalent data.
        """
        return crawlers.Source(
            name=src.name,
            code_name=src.code_name,
            type=crawlers.SourceType(src.type.value),
            url=src.url,
        )
