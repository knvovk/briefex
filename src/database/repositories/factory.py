import logging
from abc import ABC, abstractmethod
from typing import Callable, override

from ..base import Base as BaseSQLAlchemyModel
from ..exceptions import DatabaseConfigurationError
from .base import BaseRepository

logger = logging.getLogger(__name__)

ModelT = type[BaseSQLAlchemyModel]
RepoClsT = type[BaseRepository]

_registry: dict[ModelT, RepoClsT] = {}


def register(model: ModelT) -> Callable[[RepoClsT], RepoClsT]:
    def decorator(repo_cls: RepoClsT) -> RepoClsT:
        if not issubclass(repo_cls, BaseRepository):
            raise DatabaseConfigurationError(
                issue=f"{repo_cls.__name__} must inherit from BaseRepository",
                component="repository_registration",
            )

        if model in _registry:
            old_cls = _registry[model]
            logger.warning(
                "Repository for %s already registered (%s). Will be replaced by %s.",
                model.__name__,
                old_cls.__name__,
                repo_cls.__name__,
            )

        _registry[model] = repo_cls
        logger.debug("Registered %s for model %s", repo_cls.__name__, model.__name__)
        return repo_cls

    return decorator


class BaseRepositoryFactory(ABC):

    @abstractmethod
    def create(self, model: ModelT) -> BaseRepository: ...


class RepositoryFactory(BaseRepositoryFactory):

    def __init__(self) -> None:
        logger.info("RepositoryFactory ready (%d repos)", len(_registry))

    @override
    def create(self, model: ModelT) -> BaseRepository:
        repo_cls = _registry.get(model)
        if repo_cls is None:
            raise DatabaseConfigurationError(
                issue=f"No repository registered for model {model}",
                component="repository_selection",
            )

        try:
            return repo_cls()  # noqa
        except Exception as exc:
            raise DatabaseConfigurationError(
                issue=f"Unable to instantiate repository {repo_cls.__name__}: {exc}",
                component="repository_instantiation",
            ) from exc

    @staticmethod
    def registered_models() -> tuple[ModelT, ...]:
        return tuple(_registry.keys())

    @staticmethod
    def is_supported(model: ModelT) -> bool:
        return model in _registry
