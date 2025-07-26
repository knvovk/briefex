from __future__ import annotations

from briefex.storage.base import (
    PostStorage,
    PostStorageFactory,
    SourceStorage,
    SourceStorageFactory,
)
from briefex.storage.exceptions import (
    DuplicateObjectError,
    ObjectNotFoundError,
    StorageConfigurationError,
    StorageConnectionError,
    StorageException,
)
from briefex.storage.factory import (
    DefaultPostStorageFactory,
    DefaultSourceStorageFactory,
)
from briefex.storage.models import Post, PostStatus, Source, SourceType
from briefex.storage.session import init_connection

_source_storage_factory: SourceStorageFactory | None = None
_post_storage_factory: PostStorageFactory | None = None


def get_default_source_storage_factory() -> SourceStorageFactory:
    global _source_storage_factory

    if _source_storage_factory is None:
        _source_storage_factory = DefaultSourceStorageFactory()

    return _source_storage_factory


def get_default_post_storage_factory() -> PostStorageFactory:
    global _post_storage_factory

    if _post_storage_factory is None:
        _post_storage_factory = DefaultPostStorageFactory()

    return _post_storage_factory


__all__ = [
    "PostStorage",
    "PostStorageFactory",
    "SourceStorage",
    "SourceStorageFactory",
    "DuplicateObjectError",
    "ObjectNotFoundError",
    "StorageConfigurationError",
    "StorageConnectionError",
    "StorageException",
    "Post",
    "PostStatus",
    "Source",
    "SourceType",
    "init_connection",
    "get_default_source_storage_factory",
    "get_default_post_storage_factory",
]
