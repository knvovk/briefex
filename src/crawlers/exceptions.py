class CrawlerException(Exception):

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


class CrawlerConfigurationError(CrawlerException):

    def __init__(self, issue: str, component: str) -> None:
        super().__init__(
            message=f"Configuration error: {issue}",
            details={
                "issue": issue,
                "component": component,
            },
        )


class InvalidSourceError(CrawlerException):

    def __init__(self, src_url: str, reason: str) -> None:
        super().__init__(
            message=f"Invalid source: {src_url}",
            details={
                "src_url": src_url,
                "reason": reason,
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

    def __init__(self, url: str, timeout: float) -> None:
        super().__init__(
            message=f"Timeout fetching URL: {url} reached: {timeout}s",
            details={
                "url": url,
                "timeout": timeout,
            },
        )


class FetchConnectionError(FetchError):

    def __init__(self, url: str, reason: str) -> None:
        super().__init__(
            message=f"Connection error fetching URL: {url}",
            details={
                "url": url,
                "reason": reason,
            },
        )


class FetchHTTPError(FetchError):

    def __init__(self, url: str, status_code: int, reason: str) -> None:
        super().__init__(
            message=f"HTTP {status_code} error fetching URL: {url}: {reason}",
            details={
                "url": url,
                "status_code": status_code,
                "reason": reason,
            },
        )


class ParseError(CrawlerException):
    pass


class ParseContentError(ParseError):

    def __init__(self, url: str, parser_type: str, reason: str) -> None:
        super().__init__(
            message=f"Error parsing content for URL: {url} by {parser_type}",
            details={
                "url": url,
                "parser_type": parser_type,
                "reason": reason,
            },
        )


class ParseStructureError(ParseError):

    def __init__(self, url: str, actual_value: str, expected_value: str) -> None:
        super().__init__(
            message=f"Error parsing structure for URL: {url}",
            details={
                "url": url,
                "actual_value": actual_value,
                "expected_value": expected_value,
            },
        )


class PostValidationError(CrawlerException):

    def __init__(self, post_url: str, validation_errors: list[str]) -> None:
        super().__init__(
            message=f"Validation errors for post URL: {post_url}",
            details={
                "post_url": post_url,
                "validation_errors": validation_errors,
            },
        )


class PostProcessingError(CrawlerException):

    def __init__(self, url: str, stage: str, reason: str) -> None:
        super().__init__(
            message=f"Error processing post URL: {url} at stage: {stage}",
            details={
                "url": url,
                "stage": stage,
                "reason": reason,
            },
        )


class CrawlerOperationError(CrawlerException):

    def __init__(self, operation: str, src_name: str, reason: str) -> None:
        super().__init__(
            message=f"Error performing operation: {operation} for source: {src_name}",
            details={
                "operation": operation,
                "src_name": src_name,
                "reason": reason,
            },
        )


class RateLimitError(CrawlerException):

    def __init__(self, url: str, retry_after: int | None = None) -> None:
        super().__init__(
            message=f"Rate limit exceeded for URL: {url}",
            details={
                "url": url,
                "retry_after": retry_after,
            },
        )


def create_fetch_error(url: str, exc: Exception) -> FetchError:
    if "timeout" in str(exc).lower():
        return FetchTimeoutError(url, 30.0)
    elif "connection" in str(exc).lower():
        return FetchConnectionError(url, str(exc))
    else:
        return FetchError(f"Error fetching URL: {url} - {str(exc)}")


def create_parse_error(url: str, parser_type: str, exc: Exception) -> ParseError:
    if "structure" in str(exc).lower() or "schema" in str(exc).lower():
        return ParseStructureError(url, "expected structure", str(exc))
    else:
        return ParseContentError(url, parser_type, str(exc))
