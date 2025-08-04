from __future__ import annotations

import logging
from typing import override

from briefex.storage.base import (
    PostStorage,
    PostStorageFactory,
    SourceStorage,
    SourceStorageFactory,
)
from briefex.storage.exceptions import StorageConfigurationError
from briefex.storage.post import SQLAlchemyPostStorage
from briefex.storage.source import SQLAlchemySourceStorage

_log = logging.getLogger(__name__)

_default_source_storage_cls: type[SourceStorage] = SQLAlchemySourceStorage
_default_post_storage_cls: type[PostStorage] = SQLAlchemyPostStorage


class DefaultSourceStorageFactory(SourceStorageFactory):
    """Factory for creating the default SourceStorage implementation."""

    @override
    def create(self) -> SourceStorage:
        """Initialize and return the default SourceStorage.

        Returns:
            An instance of the default SourceStorage class.

        Raises:
            StorageConfigurationError: If instantiation fails.
        """
        class_name = _default_source_storage_cls.__name__
        _log.debug("Instantiating default source storage class '%s'", class_name)

        try:
            instance = _default_source_storage_cls()
            _log.info("Source storage '%s' instantiated successfully", class_name)
            return instance

        except Exception as exc:
            _log.error("Failed to instantiate source storage '%s': %s", class_name, exc)
            raise StorageConfigurationError(
                issue=f"Source storage instantiation failed for '{class_name}': {exc}",
                stage="source_storage_instantiation",
            ) from exc


class DefaultPostStorageFactory(PostStorageFactory):
    """Factory for creating the default PostStorage implementation."""

    @override
    def create(self) -> PostStorage:
        """Initialize and return the default PostStorage.

        Returns:
            An instance of the default PostStorage class.

        Raises:
            StorageConfigurationError: If instantiation fails.
        """
        class_name = _default_post_storage_cls.__name__
        _log.debug("Instantiating default post storage class '%s'", class_name)

        try:
            instance = _default_post_storage_cls()
            _log.info("Post storage '%s' instantiated successfully", class_name)
            return instance

        except Exception as exc:
            _log.error("Failed to instantiate post storage '%s': %s", class_name, exc)
            raise StorageConfigurationError(
                issue=f"Post storage instantiation failed for '{class_name}': {exc}",
                stage="post_storage_instantiation",
            ) from exc
