import re
from typing import Any, NoReturn

from sqlalchemy.exc import IntegrityError

DUPLICATE_KEY_RE: re.Pattern[str] = re.compile(
    r"duplicate key value violates unique constraint "
    r'".*?_(?P<field>\w+)_key"'
    r".*?Detail:.*?=\s*\((?P<value>.+?)\)",
    re.IGNORECASE | re.DOTALL,
)

CONSTRAINT_RE: re.Pattern[str] = re.compile(
    r"violates check constraint\s+\"(?P<constraint>[^\"]+)\"",
    re.IGNORECASE,
)


class StorageException(Exception):

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __repr__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message

    def __str__(self) -> str:
        return repr(self)


class StorageConfigurationError(StorageException):

    def __init__(self, issue: str, component: str) -> None:
        super().__init__(
            message=f"Configuration error: {issue}",
            details={
                "issue": issue,
                "component": component,
            },
        )


class StorageConnectionError(StorageException):

    def __init__(self, details: dict | None = None) -> None:
        super().__init__(
            message="Error connecting to database",
            details=details,
        )


class StorageTransactionError(StorageException):

    def __init__(self, details: dict | None = None) -> None:
        super().__init__(
            message="Error starting database transaction",
            details=details,
        )


class ModelNotFoundError(StorageException):

    def __init__(self, name: str, pk: str) -> None:
        super().__init__(
            message="Object not found",
            details={
                "name": name,
                "pk": pk,
            },
        )


class ValidationError(StorageException):

    def __init__(self, field_errors: dict[str, str] | None = None) -> None:
        super().__init__(
            message="Error validating data",
            details={
                "field_errors": (
                    ", ".join(f"{k}: {v}" for k, v in field_errors.items())
                    if field_errors
                    else ""
                ),
            },
        )


class DuplicateError(StorageException):

    def __init__(self, field_name: str, value: Any) -> None:
        super().__init__(
            message="Duplicate value" + f": {value}" if value else "",
            details={
                "field_name": field_name,
                "value": value,
            },
        )


class ConstraintViolationError(StorageException):

    def __init__(self, constraint_name: str) -> None:
        super().__init__(
            message="Constraint violation",
            details={
                "constraint_name": constraint_name,
            },
        )


class QueryExecutionError(StorageException):

    def __init__(self, query: str | None = None, reason: str | None = None) -> None:
        super().__init__(
            message="Error executing query",
            details={
                "query": query,
                "reason": reason,
            },
        )


_SQLALCHEMY_ERROR_MAPPING: dict[str, type[StorageException]] = {
    "IntegrityError": DuplicateError,
    "DataError": ValidationError,
    "OperationalError": StorageConnectionError,
    "ProgrammingError": QueryExecutionError,
}


def create_from_sa_error(exc: Exception, **details) -> StorageException:
    err_name = type(exc).__name__
    exc_cls: type[StorageException] = _SQLALCHEMY_ERROR_MAPPING.get(
        err_name, StorageException
    )

    details.setdefault("original_error", err_name)
    return exc_cls(str(exc), **details)


def create_from_integrity_err(exc: IntegrityError) -> NoReturn:
    msg = str(exc.orig)

    if m := DUPLICATE_KEY_RE.search(msg):
        field, value = m.group("field"), m.group("value")
        raise DuplicateError(field_name=field, value=value) from exc

    if m := CONSTRAINT_RE.search(msg):
        constraint = m.group("constraint")
        raise ConstraintViolationError(constraint_name=constraint) from exc

    raise create_from_sa_error(exc) from exc  # fallback
