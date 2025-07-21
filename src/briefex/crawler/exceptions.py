from __future__ import annotations


class CrawlerException(Exception):

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

    def __init__(self, issue: str, stage: str) -> None:
        super().__init__(
            message=f"Configuration error: {issue}",
            details={
                "issue": issue,
                "stage": stage,
            },
        )


class InvalidSourceError(CrawlerException):

    def __init__(self, issue: str, src_url: str | None = None) -> None:
        super().__init__(
            message=f"Invalid source: {issue}",
            details={
                "issue": issue,
                "src_url": src_url,
            },
        )


class SourceNotFoundError(CrawlerException):

    def __init__(self, src_url: str) -> None:
        super().__init__(
            message=f"Source not found: {src_url}",
            details={
                "src_url": src_url,
            },
        )


class FetchError(CrawlerException):
    pass


class FetchTimeoutError(FetchError):

    def __init__(self, src_url: str, timeout: float) -> None:
        super().__init__(
            message=f"Timeout {timeout}s reached during fetching URL: {src_url}",
            details={
                "src_url": src_url,
                "timeout": timeout,
            },
        )


class FetchConnectionError(FetchError):

    def __init__(self, issue: str, src_url: str) -> None:
        super().__init__(
            message=f"Connection error during fetching URL: {src_url}",
            details={
                "issue": issue,
                "src_url": src_url,
            },
        )


class FetchHttpError(FetchError):

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
    pass


class ParseContentError(CrawlerException):

    def __init__(self, issue: str, src_url: str) -> None:
        super().__init__(
            message=f"Error parsing content for URL: {src_url}",
            details={
                "issue": issue,
                "src_url": src_url,
            },
        )


class ParseStructureError(CrawlerException):
    def __init__(self, issue: str, src_url: str) -> None:
        super().__init__(
            message=f"Error parsing structure for URL: {src_url}",
            details={
                "issue": issue,
                "src_url": src_url,
            },
        )
