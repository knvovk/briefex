from __future__ import annotations


class CrawlerException(Exception):
    """Base exception for crawler errors, with message and optional details."""

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


class CrawlerConfigurationError(CrawlerException):
    """Raised for invalid crawler configuration."""

    def __init__(self, issue: str, stage: str) -> None:
        super().__init__(
            message=f"Configuration error: {issue}",
            details={
                "issue": issue,
                "stage": stage,
            },
        )


class InvalidSourceError(CrawlerException):
    """Raised when a source URL is invalid."""

    def __init__(self, issue: str, src_url: str | None = None) -> None:
        super().__init__(
            message=f"Invalid source: {issue}",
            details={
                "issue": issue,
                "src_url": src_url,
            },
        )


class SourceNotFoundError(CrawlerException):
    """Raised when the specified source URL is not found."""

    def __init__(self, src_url: str) -> None:
        super().__init__(
            message=f"Source not found: {src_url}",
            details={
                "src_url": src_url,
            },
        )


class FetchError(CrawlerException):
    """Base exception for fetch-related errors."""


class FetchTimeoutError(FetchError):
    """Raised when fetching a URL times out."""

    def __init__(self, src_url: str, timeout: float) -> None:
        super().__init__(
            message=f"Timeout {timeout}s reached during fetching URL: {src_url}",
            details={
                "src_url": src_url,
                "timeout": timeout,
            },
        )


class FetchConnectionError(FetchError):
    """Raised on connection errors during fetching."""

    def __init__(self, issue: str, src_url: str) -> None:
        super().__init__(
            message=f"Connection error during fetching URL: {src_url}",
            details={
                "issue": issue,
                "src_url": src_url,
            },
        )


class FetchHttpError(FetchError):
    """Raised on HTTP status errors during fetching."""

    def __init__(
        self,
        issue: str,
        src_url: str,
        status_code: int | None = None,
    ) -> None:
        super().__init__(
            message=f"HTTP error during fetching URL: {src_url}",
            details={
                "issue": issue,
                "src_url": src_url,
                "status_code": status_code,
            },
        )


class ParseError(CrawlerException):
    """Base exception for parse-related errors."""


class ParseContentError(ParseError):
    """Raised when parsing content fails."""

    def __init__(self, issue: str, src_url: str) -> None:
        super().__init__(
            message=f"Error parsing content for URL: {src_url}",
            details={
                "issue": issue,
                "src_url": src_url,
            },
        )


class ParseStructureError(ParseError):
    """Raised when parsing HTML structure fails."""

    def __init__(self, issue: str, src_url: str) -> None:
        super().__init__(
            message=f"Error parsing structure for URL: {src_url}",
            details={
                "issue": issue,
                "src_url": src_url,
            },
        )
