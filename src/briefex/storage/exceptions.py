from __future__ import annotations


class StorageError(Exception):
    """Base exception for storage operations with message and optional details."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __repr__(self) -> str:
        if self.details:
            return f"{self.message} ({self.details!r})"
        return self.message

    def __str__(self) -> str:
        return repr(self)


class StorageConfigurationError(StorageError):
    """Raised when storage configuration is invalid."""

    def __init__(self, issue: str, stage: str) -> None:
        super().__init__(
            message=f"Configuration error: {issue}",
            details={
                "issue": issue,
                "stage": stage,
            },
        )


class StorageConnectionError(StorageError):
    """Raised when connection to storage fails."""

    def __init__(self, issue: str) -> None:
        super().__init__(
            message=f"Connection error: {issue}",
            details={
                "issue": issue,
            },
        )


class ObjectNotFoundError(StorageError):
    """Raised when a requested object is not found in storage."""

    def __init__(self, cls: str, details: dict | None = None) -> None:
        super().__init__(
            message=f"Object: {cls} not found",
            details=details or {},
        )


class DuplicateObjectError(StorageError):
    """Raised when attempting to create a duplicate object in storage."""

    def __init__(self, cls: str, details: dict | None = None) -> None:
        super().__init__(
            message=f"Object: {cls} duplicate",
            details=details or {},
        )
