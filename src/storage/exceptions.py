import re
from typing import Any, NoReturn

from sqlalchemy.exc import IntegrityError

"""
Regular expression pattern to extract field name and value
from duplicate key error messages.
"""
DUPLICATE_KEY_RE: re.Pattern[str] = re.compile(
    r"duplicate key value violates unique constraint "
    r'".*?_(?P<field>\w+)_key"'
    r".*?Detail:.*?=\s*\((?P<value>.+?)\)",
    re.IGNORECASE | re.DOTALL,
)

"""
Regular expression pattern to extract constraint name
from constraint violation error messages.
"""
CONSTRAINT_RE: re.Pattern[str] = re.compile(
    r"violates check constraint\s+\"(?P<constraint>[^\"]+)\"",
    re.IGNORECASE,
)


class StorageException(Exception):
    """Base exception class for storage-related errors.

    All other storage exceptions inherit from this class.

    Attributes:
        message: A human-readable error message.
        details: A dictionary with additional error details.
    """

    def __init__(self, message: str, details: dict | None = None) -> None:
        """Initialize a new StorageException.

        Args:
            message: A human-readable error message.
            details: A dictionary with additional error details.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __repr__(self) -> str:
        """Return a string representation of the exception.

        Returns:
            A string containing the error message and details (if any).
        """
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message

    def __str__(self) -> str:
        """Return a string representation of the exception.

        Returns:
            A string containing the error message and details (if any).
        """
        return repr(self)


class StorageConfigurationError(StorageException):
    """Exception raised when there's a configuration error in the storage component.

    Attributes:
        message: A human-readable error message.
        details: A dictionary with additional error details
                 including the issue and component.
    """

    def __init__(self, issue: str, component: str) -> None:
        """Initialize a new StorageConfigurationError.

        Args:
            issue: Description of the configuration issue.
            component: The component where the configuration error occurred.
        """
        super().__init__(
            message=f"Configuration error: {issue}",
            details={
                "issue": issue,
                "component": component,
            },
        )


class StorageConnectionError(StorageException):
    """Exception raised when there's an error connecting to the database.

    Attributes:
        message: A human-readable error message.
        details: A dictionary with additional error details.
    """

    def __init__(self, details: dict | None = None) -> None:
        """Initialize a new StorageConnectionError.

        Args:
            details: A dictionary with additional error details.
        """
        super().__init__(
            message="Error connecting to database",
            details=details,
        )


class StorageTransactionError(StorageException):
    """Exception raised when there's an error starting a database transaction.

    Attributes:
        message: A human-readable error message.
        details: A dictionary with additional error details.
    """

    def __init__(self, details: dict | None = None) -> None:
        """Initialize a new StorageTransactionError.

        Args:
            details: A dictionary with additional error details.
        """
        super().__init__(
            message="Error starting database transaction",
            details=details,
        )


class ModelNotFoundError(StorageException):
    """Exception raised when a requested model object is not found in the database.

    Attributes:
        message: A human-readable error message.
        details: A dictionary with additional error details including
                 the model name and primary key.
    """

    def __init__(self, name: str, pk: str) -> None:
        """Initialize a new ModelNotFoundError.

        Args:
            name: The name of the model class.
            pk: The primary key value of the requested object.
        """
        super().__init__(
            message="Object not found",
            details={
                "name": name,
                "pk": pk,
            },
        )


class ValidationError(StorageException):
    """Exception raised when data validation fails.

    Attributes:
        message: A human-readable error message.
        details: A dictionary with additional error details
                 including field-specific errors.
    """

    def __init__(self, field_errors: dict[str, str] | None = None) -> None:
        """Initialize a new ValidationError.

        Args:
            field_errors: A dictionary mapping field names to error messages.
        """
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
    """Exception raised when a unique constraint is violated.

    This typically happens when trying to insert a record with a value
    that already exists in a field with a unique constraint.

    Attributes:
        message: A human-readable error message.
        details: A dictionary with additional error details including
                 the field name and value.
    """

    def __init__(self, field_name: str, value: Any) -> None:
        """Initialize a new DuplicateError.

        Args:
            field_name: The name of the field with the duplicate value.
            value: The duplicate value.
        """
        super().__init__(
            message="Duplicate value" + f": {value}" if value else "",
            details={
                "field_name": field_name,
                "value": value,
            },
        )


class ConstraintViolationError(StorageException):
    """Exception raised when a database constraint is violated.

    This typically happens when trying to insert or update a record that violates
    a check constraint defined in the database.

    Attributes:
        message: A human-readable error message.
        details: A dictionary with additional error
                 details including the constraint name.
    """

    def __init__(self, constraint_name: str) -> None:
        """Initialize a new ConstraintViolationError.

        Args:
            constraint_name: The name of the violated constraint.
        """
        super().__init__(
            message="Constraint violation",
            details={
                "constraint_name": constraint_name,
            },
        )


class QueryExecutionError(StorageException):
    """Exception raised when there's an error executing a database query.

    Attributes:
        message: A human-readable error message.
        details: A dictionary with additional error details
                 including the query and reason.
    """

    def __init__(self, query: str | None = None, reason: str | None = None) -> None:
        """Initialize a new QueryExecutionError.

        Args:
            query: The SQL query that failed.
            reason: The reason for the failure.
        """
        super().__init__(
            message="Error executing query",
            details={
                "query": query,
                "reason": reason,
            },
        )


def create_from_integrity_err(exc: IntegrityError) -> NoReturn:
    """Create and raise a specific exception from an IntegrityError.

    This function parses the error message to determine the specific type
    of integrity error and raises an appropriate exception.

    Args:
        exc: The original IntegrityError.

    Raises:
        DuplicateError: If the error is due to a duplicate key.
        ConstraintViolationError: If the error is due to a constraint violation.
        StorageException: For other types of integrity errors.
    """
    msg = str(exc.orig)

    if m := DUPLICATE_KEY_RE.search(msg):
        field, value = m.group("field"), m.group("value")
        raise DuplicateError(field_name=field, value=value) from exc

    if m := CONSTRAINT_RE.search(msg):
        constraint = m.group("constraint")
        raise ConstraintViolationError(constraint_name=constraint) from exc

    raise StorageException(msg) from exc  # fallback
