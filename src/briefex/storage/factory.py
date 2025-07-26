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
        _log.debug(
            "Initializing source storage by default: %s",
            _default_source_storage_cls.__name__,
        )
        try:
            instance = _default_source_storage_cls()
            _log.info(
                "%s initialized as default source storage",
                _default_source_storage_cls.__name__,
            )
            return instance

        except Exception as exc:
            _log.error("Unexpected error during source storage initialization: %s", exc)
            cls = _default_source_storage_cls.__name__
            raise StorageConfigurationError(
                issue=f"SourceStorage instantiation failed for {cls}: {exc}",
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
        _log.debug(
            "Initializing post storage by default: %s",
            _default_post_storage_cls.__name__,
        )
        try:
            instance = _default_post_storage_cls()
            _log.info(
                "%s initialized as default post storage",
                _default_post_storage_cls.__name__,
            )
            return instance

        except Exception as exc:
            _log.error("Unexpected error during post storage initialization: %s", exc)
            cls = _default_post_storage_cls.__name__
            raise StorageConfigurationError(
                issue=f"PostStorage instantiation failed for {cls}: {exc}",
                stage="post_storage_instantiation",
            ) from exc
