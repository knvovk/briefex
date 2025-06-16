from typing import Any


class DatabaseError(Exception):

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __repr__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConnectionError(DatabaseError):  # noqa

    def __init__(self, *args, **kwargs) -> None:
        message = "Error connecting to database"
        super().__init__(message, *args, **kwargs)


class TransactionError(DatabaseError):

    def __init__(self, *args, **kwargs) -> None:
        message = "Error starting database transaction"
        super().__init__(message, *args, **kwargs)


class ModelNotFoundError(DatabaseError):

    def __init__(self, m_name: str, m_pk: str, message: str | None = None) -> None:
        if message is None:
            message = f"Object {m_name} with PK {m_pk} not found"
        details = {"m_name": m_name, "m_pk": m_pk}
        super().__init__(message, details)


class ValidationError(DatabaseError):

    def __init__(self, field_errors: dict, message: str | None = None) -> None:
        if message is None:
            message = "Error validating data"
        details = {"field_errors": field_errors}
        super().__init__(message, details)


class DuplicateError(DatabaseError):

    def __init__(self, field_name: str, value: Any, message: str | None = None) -> None:
        if message is None:
            message = f"Duplicate value for field {field_name}: {value}"
        details = {"field_name": field_name, "value": value}
        super().__init__(message, details)


class ConstraintViolationError(DatabaseError):

    def __init__(self, constraint_name: str, message: str | None = None) -> None:
        if message is None:
            message = f"Constraint violation for constraint {constraint_name}"
        details = {"constraint_name": constraint_name}
        super().__init__(message, details)


class QueryExecutionError(DatabaseError):

    def __init__(
        self,
        query: str,
        error_details: str | None = None,
        message: str | None = None,
    ) -> None:
        if message is None:
            message = f"Error executing query: {query}"
        details = {"query": query}
        if error_details:
            details["error_details"] = error_details
        super().__init__(message, details)


class DatabaseConfigurationError(DatabaseError):

    def __init__(self, issue: str, component: str) -> None:
        message = f"Configuration error: {issue}"
        details = {
            "issue": issue,
            "component": component,
        }
        super().__init__(message, details)


SQLALCHEMY_ERROR_MAPPING = {
    "IntegrityError": DuplicateError,
    "DataError": ValidationError,
    "OperationalError": ConnectionError,
    "ProgrammingError": QueryExecutionError,
}


def map_sqlalchemy_error(exc: Exception, **kwargs) -> DatabaseError:
    error_type = type(exc).__name__
    custom_exception_class = SQLALCHEMY_ERROR_MAPPING.get(error_type, DatabaseError)

    message = str(exc)
    details = kwargs.get("details", {})
    details["original_error"] = error_type

    return custom_exception_class(message, details=details)
