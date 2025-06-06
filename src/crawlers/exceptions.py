class CrawlerError(Exception):

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


class SourceError(CrawlerError):
    pass


class InvalidSourceError(SourceError):

    def __init__(self, source_url: str, reason: str) -> None:
        message = f"Invalid source: {source_url}"
        details = {"source_url": source_url, "reason": reason}
        super().__init__(message, details)


class SourceNotFoundError(SourceError):

    def __init__(self, source_url: str) -> None:
        message = f"Source not found: {source_url}"
        details = {"source_url": source_url}
        super().__init__(message, details)


class FetchError(CrawlerError):
    pass


class FetchTimeoutError(FetchError):

    def __init__(self, url: str, timeout: float) -> None:
        message = f"Timeout fetching URL: {url} (timeout={timeout}s)"
        details = {"url": url, "timeout": timeout}
        super().__init__(message, details)


class FetchConnectionError(FetchError):

    def __init__(self, url: str, error_details: str) -> None:
        message = f"Connection error fetching URL: {url}"
        details = {"url": url, "error_details": error_details}
        super().__init__(message, details)


class FetchHTTPError(FetchError):

    def __init__(self, url: str, status_code: int, reason: str) -> None:
        message = f"HTTP {status_code} error fetching URL: {url} - {reason}"
        details = {"url": url, "status_code": status_code, "reason": reason}
        super().__init__(message, details)


class ParseError(CrawlerError):
    pass


class ParseContentError(ParseError):

    def __init__(self, url: str, parser_type: str, reason: str) -> None:
        message = f"Error parsing content for URL: {url} (parser={parser_type})"
        details = {"url": url, "parser_type": parser_type, "reason": reason}
        super().__init__(message, details)


class ParseStructureError(ParseError):

    def __init__(self, url: str, expected_structure: str, found_structure: str) -> None:
        message = f"Error parsing structure for URL: {url}"
        details = {
            "url": url,
            "expected_structure": expected_structure,
            "found_structure": found_structure,
        }
        super().__init__(message, details)


class PostError(CrawlerError):
    pass


class PostValidationError(PostError):

    def __init__(self, post_url: str, validation_errors: list[str]) -> None:
        message = f"Validation errors for post URL: {post_url}"
        details = {"post_url": post_url, "validation_errors": validation_errors}
        super().__init__(message, details)


class PostProcessingError(PostError):

    def __init__(self, post_url: str, processing_stage: str, error_details: str) -> None:
        message = f"Error processing post URL: {post_url} (stage={processing_stage})"
        details = {
            "post_url": post_url,
            "processing_stage": processing_stage,
            "error_details": error_details,
        }
        super().__init__(message, details)


class CrawlerConfigurationError(CrawlerError):

    def __init__(self, issue: str, component: str) -> None:
        message = f"Configuration error: {issue}"
        details = {
            "issue": issue,
            "component": component,
        }
        super().__init__(message, details)


class CrawlerOperationError(CrawlerError):

    def __init__(self, operation: str, source_name: str, error_details: str) -> None:
        message = f"Error performing operation: {operation} for source: {source_name}"
        details = {
            "operation": operation,
            "source_name": source_name,
            "error_details": error_details,
        }
        super().__init__(message, details)


class RateLimitError(CrawlerError):

    def __init__(self, url: str, retry_after: int | None = None) -> None:
        message = f"Rate limit exceeded for URL: {url}"
        details = {"url": url}
        if retry_after:
            details["retry_after"] = retry_after
            message += f" (retry after {retry_after} seconds)"
        super().__init__(message, details)


def create_fetch_error(url: str, error: Exception) -> FetchError:
    if "timeout" in str(error).lower():
        return FetchTimeoutError(url, 30.0)
    elif "connection" in str(error).lower():
        return FetchConnectionError(url, str(error))
    else:
        return FetchError(f"Error fetching URL: {url} - {str(error)}")


def create_parse_error(url: str, parser_type: str, error: Exception) -> ParseError:
    if "structure" in str(error).lower() or "schema" in str(error).lower():
        return ParseStructureError(url, "expected structure", str(error))
    else:
        return ParseContentError(url, parser_type, str(error))
