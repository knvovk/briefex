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


class DatabaseError(Exception):
    default_message: str = "Database error"

    def __init__(self, message: str | None = None, **details: Any) -> None:
        message = message or self.default_message
        super().__init__(message)

        self.message: str = message
        self.details: dict[str, Any] = details

    def __repr__(self) -> str:
        return (
            f"{self.message} | Details: {self.details}"
            if self.details
            else self.message
        )

    def __str__(self) -> str:
        return self.message


class ConnectionError(DatabaseError):  # noqa
    default_message = "Error connecting to database"


class TransactionError(DatabaseError):
    default_message = "Error starting database transaction"


class ModelNotFoundError(DatabaseError):
    default_message = "Object not found"

    def __init__(
        self,
        message: str | None = None,
        *,
        name: str | None = None,
        pk: str | None = None,
        **details: Any,
    ) -> None:
        if name is not None:
            details["name"] = name
        if pk is not None:
            details["pk"] = pk
        super().__init__(message or self.default_message, **details)


class ValidationError(DatabaseError):
    default_message = "Error validating data"

    def __init__(
        self,
        message: str | None = None,
        *,
        field_errors: dict[str, str] | None = None,
        **details: Any,
    ) -> None:
        if field_errors:
            details["field_errors"] = ", ".join(
                f"{k}: {v}" for k, v in field_errors.items()
            )
        super().__init__(message or self.default_message, **details)


class DuplicateError(DatabaseError):
    default_message = "Duplicate value"

    def __init__(
        self,
        message: str | None = None,
        *,
        field_name: str | None = None,
        value: Any | None = None,
        **details: Any,
    ) -> None:
        msg = message or self.default_message

        if field_name:
            msg += f" for field {field_name}"
            details["field_name"] = field_name
            if value is not None:
                msg += f": {value}"
                details["value"] = value

        super().__init__(msg, **details)


class ConstraintViolationError(DatabaseError):
    default_message = "Constraint violation"

    def __init__(
        self,
        message: str | None = None,
        *,
        constraint_name: str | None = None,
        **details: Any,
    ) -> None:
        if constraint_name:
            details["constraint_name"] = constraint_name
        super().__init__(message or self.default_message, **details)


class QueryExecutionError(DatabaseError):
    default_message = "Error executing query"

    def __init__(
        self,
        message: str | None = None,
        *,
        query: str | None = None,
        error_details: str | None = None,
        **details: Any,
    ) -> None:
        if query:
            details["query"] = query
        if error_details:
            details["error_details"] = error_details
        super().__init__(message or self.default_message, **details)


class StorageConfigurationError(DatabaseError):
    default_message = "Configuration error"

    def __init__(
        self,
        message: str | None = None,
        *,
        issue: str | None = None,
        component: str | None = None,
        **details: Any,
    ) -> None:
        if issue:
            details["issue"] = issue
        if component:
            details["component"] = component
        super().__init__(message or self.default_message, **details)


_SQLALCHEMY_ERROR_MAPPING: dict[str, type[DatabaseError]] = {
    "IntegrityError": DuplicateError,
    "DataError": ValidationError,
    "OperationalError": ConnectionError,
    "ProgrammingError": QueryExecutionError,
}


def map_sqlalchemy_error(exc: Exception, **details) -> DatabaseError:
    err_name = type(exc).__name__
    exc_cls: type[DatabaseError] = _SQLALCHEMY_ERROR_MAPPING.get(
        err_name, DatabaseError
    )

    details.setdefault("original_error", err_name)
    return exc_cls(str(exc), **details)


def handle_integrity_err(exc: IntegrityError) -> NoReturn:
    msg = str(exc.orig)

    if m := DUPLICATE_KEY_RE.search(msg):
        field, value = m.group("field"), m.group("value")
        raise DuplicateError(field_name=field, value=value) from exc

    if m := CONSTRAINT_RE.search(msg):
        constraint = m.group("constraint")
        raise ConstraintViolationError(constraint_name=constraint) from exc

    raise map_sqlalchemy_error(exc) from exc  # fallback
