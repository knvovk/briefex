class CrawlerException(Exception):
    """Base exception class for all crawler exceptions.

    This class provides a common interface for all crawler exceptions,
    including a message and optional details.

    Attributes:
        message: A descriptive error message.
        details: A dictionary of additional details about the error.
    """

    def __init__(self, message: str, details: dict | None = None) -> None:
        """Initialize a new CrawlerException.

        Args:
            message: A descriptive error message.
            details: A dictionary of additional details about the error.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __repr__(self) -> str:
        """Get a string representation of the exception.

        Returns:
            A string representation of the exception, including details if available.
        """
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message

    def __str__(self) -> str:
        """Get a string representation of the exception.

        Returns:
            A string representation of the exception.
        """
        return repr(self)


class CrawlerConfigurationError(CrawlerException):
    """Exception raised for configuration errors in the crawler.

    This exception is raised when there is an error in the configuration
    of a crawler component.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the issue and component.
    """

    def __init__(self, issue: str, component: str) -> None:
        """Initialize a new CrawlerConfigurationError.

        Args:
            issue: A description of the configuration issue.
            component: The name of the component with the configuration issue.
        """
        super().__init__(
            message=f"Configuration error: {issue}",
            details={
                "issue": issue,
                "component": component,
            },
        )


class InvalidSourceError(CrawlerException):
    """Exception raised when a source is invalid.

    This exception is raised when a source URL is invalid or cannot be processed.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the source URL and reason.
    """

    def __init__(self, src_url: str, reason: str) -> None:
        """Initialize a new InvalidSourceError.

        Args:
            src_url: The URL of the invalid source.
            reason: The reason why the source is invalid.
        """
        super().__init__(
            message=f"Invalid source: {src_url}",
            details={
                "src_url": src_url,
                "reason": reason,
            },
        )


class SourceNotFoundError(CrawlerException):
    """Exception raised when a source is not found.

    This exception is raised when a source URL cannot be found or accessed.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the source URL.
    """

    def __init__(self, src_url: str) -> None:
        """Initialize a new SourceNotFoundError.

        Args:
            src_url: The URL of the source that was not found.
        """
        super().__init__(
            message=f"Source not found: {src_url}",
            details={
                "src_url": src_url,
            },
        )


class FetchError(CrawlerException):
    """Base exception class for fetch errors.

    This exception is raised when there is an error fetching content from a URL.
    It serves as a base class for more specific fetch error types.
    """

    pass


class FetchTimeoutError(FetchError):
    """Exception raised when a fetch operation times out.

    This exception is raised when a fetch operation exceeds the specified timeout.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the URL and timeout.
    """

    def __init__(self, url: str, timeout: float) -> None:
        """Initialize a new FetchTimeoutError.

        Args:
            url: The URL that was being fetched.
            timeout: The timeout in seconds that was exceeded.
        """
        super().__init__(
            message=f"Timeout fetching URL: {url} reached: {timeout}s",
            details={
                "url": url,
                "timeout": timeout,
            },
        )


class FetchConnectionError(FetchError):
    """Exception raised when there is a connection error during fetch.

    This exception is raised when there is an error establishing a connection
    to the URL being fetched.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the URL and reason for the error.
    """

    def __init__(self, url: str, reason: str) -> None:
        """Initialize a new FetchConnectionError.

        Args:
            url: The URL that was being fetched.
            reason: The reason for the connection error.
        """
        super().__init__(
            message=f"Connection error fetching URL: {url}",
            details={
                "url": url,
                "reason": reason,
            },
        )


class FetchHTTPError(FetchError):
    """Exception raised when an HTTP error occurs during fetch.

    This exception is raised when an HTTP request returns an error status code.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the URL, status code, and reason.
    """

    def __init__(self, url: str, status_code: int, reason: str) -> None:
        """Initialize a new FetchHTTPError.

        Args:
            url: The URL that was being fetched.
            status_code: The HTTP status code that was returned.
            reason: The reason for the HTTP error.
        """
        super().__init__(
            message=f"HTTP {status_code} error fetching URL: {url}: {reason}",
            details={
                "url": url,
                "status_code": status_code,
                "reason": reason,
            },
        )


class ParseError(CrawlerException):
    """Base exception class for parse errors.

    This exception is raised when there is an error parsing content.
    It serves as a base class for more specific parse error types.
    """

    pass


class ParseContentError(ParseError):
    """Exception raised when there is an error parsing content.

    This exception is raised when a parser encounters an error while
    parsing the content of a URL.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the URL, parser type, and reason.
    """

    def __init__(self, url: str, parser_type: str, reason: str) -> None:
        """Initialize a new ParseContentError.

        Args:
            url: The URL whose content was being parsed.
            parser_type: The type of parser that encountered the error.
            reason: The reason for the parsing error.
        """
        super().__init__(
            message=f"Error parsing content for URL: {url} by {parser_type}",
            details={
                "url": url,
                "parser_type": parser_type,
                "reason": reason,
            },
        )


class ParseStructureError(ParseError):
    """Exception raised when there is an error parsing the structure of content.

    This exception is raised when a parser encounters an error with the
    structure of the content, such as missing expected elements.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the URL, actual value, and expected value.
    """

    def __init__(self, url: str, actual_value: str, expected_value: str) -> None:
        """Initialize a new ParseStructureError.

        Args:
            url: The URL whose content was being parsed.
            actual_value: The actual value that was found.
            expected_value: The value that was expected.
        """
        super().__init__(
            message=f"Error parsing structure for URL: {url}",
            details={
                "url": url,
                "actual_value": actual_value,
                "expected_value": expected_value,
            },
        )


class PostValidationError(CrawlerException):
    """Exception raised when a post fails validation.

    This exception is raised when a post does not meet the validation criteria.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the post-URL and validation errors.
    """

    def __init__(self, post_url: str, validation_errors: list[str]) -> None:
        """Initialize a new PostValidationError.

        Args:
            post_url: The URL of the post that failed validation.
            validation_errors: A list of validation error messages.
        """
        super().__init__(
            message=f"Validation errors for post URL: {post_url}",
            details={
                "post_url": post_url,
                "validation_errors": validation_errors,
            },
        )


class PostProcessingError(CrawlerException):
    """Exception raised when there is an error processing a post.

    This exception is raised when an error occurs during post-processing.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the URL, processing stage, and reason.
    """

    def __init__(self, url: str, stage: str, reason: str) -> None:
        """Initialize a new PostProcessingError.

        Args:
            url: The URL of the post that was being processed.
            stage: The processing stage where the error occurred.
            reason: The reason for the processing error.
        """
        super().__init__(
            message=f"Error processing post URL: {url} at stage: {stage}",
            details={
                "url": url,
                "stage": stage,
                "reason": reason,
            },
        )


class CrawlerOperationError(CrawlerException):
    """Exception raised when there is an error performing a crawler operation.

    This exception is raised when an error occurs during a crawler operation.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the operation, source name, and reason.
    """

    def __init__(self, operation: str, src_name: str, reason: str) -> None:
        """Initialize a new CrawlerOperationError.

        Args:
            operation: The operation that was being performed.
            src_name: The name of the source being processed.
            reason: The reason for the operation error.
        """
        super().__init__(
            message=f"Error performing operation: {operation} for source: {src_name}",
            details={
                "operation": operation,
                "src_name": src_name,
                "reason": reason,
            },
        )


class RateLimitError(CrawlerException):
    """Exception raised when a rate limit is exceeded.

    This exception is raised when a request exceeds the rate limit of a server.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the URL and retry-after time.
    """

    def __init__(self, url: str, retry_after: int | None = None) -> None:
        """Initialize a new RateLimitError.

        Args:
            url: The URL that exceeded the rate limit.
            retry_after: The number of seconds to wait before retrying, if provided.
        """
        super().__init__(
            message=f"Rate limit exceeded for URL: {url}",
            details={
                "url": url,
                "retry_after": retry_after,
            },
        )


def create_fetch_error(url: str, exc: Exception) -> FetchError:
    """Create a specific fetch error based on the exception.

    This function examines the exception message to determine the type of fetch error
    and creates a more specific exception with additional context.

    Args:
        url: The URL that was being fetched.
        exc: The exception raised during fetching.

    Returns:
        A more specific FetchError subclass if the exception type is recognized,
        or a generic FetchError otherwise.
    """
    if "timeout" in str(exc).lower():
        return FetchTimeoutError(url, 30.0)
    elif "connection" in str(exc).lower():
        return FetchConnectionError(url, str(exc))
    else:
        return FetchError(f"Error fetching URL: {url} - {str(exc)}")


def create_parse_error(url: str, parser_type: str, exc: Exception) -> ParseError:
    """Create a specific parse error based on the exception.

    This function examines the exception message to determine the type of parse error
    and creates a more specific exception with additional context.

    Args:
        url: The URL whose content was being parsed.
        parser_type: The type of parser that encountered the error.
        exc: The exception raised during parsing.

    Returns:
        A more specific ParseError subclass if the exception type is recognized,
        or a generic ParseContentError otherwise.
    """
    if "structure" in str(exc).lower() or "schema" in str(exc).lower():
        return ParseStructureError(url, "expected structure", str(exc))
    else:
        return ParseContentError(url, parser_type, str(exc))
