import logging
import random
import time
from typing import override
from urllib.parse import urlparse

import requests
import requests.adapters
from pydantic import BaseModel
from requests.exceptions import ConnectionError, RequestException, Timeout

from ..exceptions import (
    CrawlerConfigurationError,
    FetchConnectionError,
    FetchError,
    FetchHTTPError,
    FetchTimeoutError,
    InvalidSourceError,
    RateLimitError,
    SourceNotFoundError,
)
from ..models import SourceType
from ..utils import humanize_filesize
from .base import Fetcher
from .registry import register

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Edge/120.0.2210.91 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]


class HTTPStatusCode:
    """HTTP status code constants.

    This class provides constants for common HTTP status codes used in the fetcher.
    """

    OK = 200
    FOUND = 302
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


class Config(BaseModel):
    """Configuration for the HTML fetcher.

    This class defines the configuration parameters for the HTML fetcher,
    including timeouts, connection pool settings, and retry behavior.

    Attributes:
        user_agents: List of user agent strings to use for requests.
        req_timeout: Timeout in seconds for HTTP requests.
        pool_conn: Number of connection objects to keep in the pool.
        pool_max_size: Maximum number of connections to keep in the pool.
        max_retries: Maximum number of retry attempts for failed requests.
        retry_delay: Base delay in seconds between retry attempts.
        max_retry_delay: Maximum delay in seconds between retry attempts.
    """

    user_agents: list[str]
    req_timeout: int
    pool_conn: int
    pool_max_size: int
    max_retries: int
    retry_delay: float
    max_retry_delay: float


def _build_config(kwargs: dict) -> Config:
    """Build a Config object from keyword arguments.

    This function creates a Config object using the provided keyword arguments,
    with default values for missing parameters.

    Args:
        kwargs: Dictionary of configuration parameters.

    Returns:
        A Config object with the specified parameters.

    Raises:
        CrawlerConfigurationError: If the configuration parameters are invalid.
    """
    try:
        return Config(
            user_agents=kwargs.get("user_agents") or USER_AGENTS,
            req_timeout=kwargs.get("req_timeout"),
            pool_conn=kwargs.get("pool_conn"),
            pool_max_size=kwargs.get("pool_max_size"),
            max_retries=kwargs.get("max_retries"),
            retry_delay=kwargs.get("retry_delay"),
            max_retry_delay=kwargs.get("max_retry_delay"),
        )
    except Exception as exc:
        raise CrawlerConfigurationError(
            issue=f"Invalid configuration parameters: {exc}",
            component="fetcher_configuration",
        ) from exc


def _validate_url(url: str) -> None:
    """Validate a URL for fetching.

    This function checks that a URL is valid for fetching, including
    - Not empty
    - Uses HTTP or HTTPS scheme
    - Contains a valid domain
    - Does not contain invalid whitespace characters

    Args:
        url: The URL to validate.

    Raises:
        InvalidSourceError: If the URL is invalid.
    """
    if not url or not url.strip():
        raise InvalidSourceError("", "URL cannot be empty")

    url = url.strip()
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise InvalidSourceError(url, "URL must use HTTP or HTTPS scheme")

    if not parsed.netloc:
        raise InvalidSourceError(url, "URL must contain a valid domain")

    # Check for invalid characters
    invalid_chars = {" ", "\n", "\r", "\t"}
    if any(char in url for char in invalid_chars):
        raise InvalidSourceError(url, "URL contains invalid whitespace characters")


def _parse_retry_after(retry_after: str | None) -> int | None:
    """Parse the Retry-After header value.

    This function attempts to parse the Retry-After header value from an HTTP response.

    Args:
        retry_after: The value of the Retry-After header, or None if not present.

    Returns:
        The number of seconds to wait before retrying, or None if the header is
        missing or invalid.
    """
    if not retry_after:
        return None

    try:
        return int(retry_after)
    except ValueError:
        logger.debug("Invalid Retry-After header value: %s", retry_after)
        return None


@register(SourceType.HTML)
class HTMLFetcher(Fetcher):
    """Fetcher for HTML sources.

    This fetcher is responsible for retrieving content from HTML web pages.
    It handles HTTP requests, retries, and error handling.

    Attributes:
        _session: The requests session used for making HTTP requests.
        _config: Configuration parameters for the fetcher.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initialize a new HTMLFetcher.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments for configuration.
                Supported keys:
                - user_agents: List of user agent strings
                - request_timeout: Timeout in seconds for HTTP requests
                - pool_connections: Number of connection objects to keep in pool
                - pool_maxsize: Maximum number of connections to keep in pool
                - max_retries: Maximum number of retry attempts
                - retry_delay: Base delay in seconds between retry attempts
                - max_retry_delay: Maximum delay in seconds between retry attempts
        """
        super().__init__(*args, **kwargs)
        self._session: requests.Session | None = None
        self._config = _build_config(kwargs)
        self._setup_session()

    @override
    def fetch(self, url: str) -> bytes:
        """Fetch content from a URL.

        This method validates the URL, sets up headers with a random user agent,
        and fetches the content with retries.

        Args:
            url: The URL to fetch content from.

        Returns:
            The fetched content as bytes.

        Raises:
            InvalidSourceError: If the URL is invalid.
            FetchError: If the content cannot be fetched.
        """
        logger.info("Fetching HTML content from %s", url)
        _validate_url(url)
        headers = {"User-Agent": self._get_random_user_agent()}
        return self._fetch_with_retries(url, headers)

    def _fetch_with_retries(self, url: str, headers: dict[str, str]) -> bytes:
        """Fetch content from a URL with retry logic.

        This method attempts to fetch content from a URL, with retries for
        certain types of failures (timeouts, connection errors).

        Args:
            url: The URL to fetch content from.
            headers: HTTP headers to include in the request.

        Returns:
            The fetched content as bytes.

        Raises:
            FetchError: If all retry attempts fail.
            RateLimitError: If the server indicates rate limiting.
            FetchHTTPError: If an HTTP error occurs.
            SourceNotFoundError: If the source is not found.
        """
        last_exception = None
        for attempt in range(1, self._config.max_retries + 1):
            try:
                if attempt > 1:
                    logger.debug(
                        "Attempt %d/%d for %s",
                        attempt,
                        self._config.max_retries,
                        url,
                    )
                response = self._make_request(url, headers=headers)
                self._log_response_info(url, response)
                logger.info(
                    "Successfully fetched %s (status=%d, attempt=%d)",
                    url,
                    response.status_code,
                    attempt,
                )
                return response.content

            except (FetchTimeoutError, FetchConnectionError) as exc:
                last_exception = exc
                if self._should_retry(attempt):
                    delay = self._calculate_retry_delay(attempt)
                    logger.warning(
                        "Attempt %d failed for %s: %s. Retrying in %.1fs",
                        attempt,
                        url,
                        exc,
                        delay,
                    )
                    time.sleep(delay)
                    continue
                break

            except (RateLimitError, FetchHTTPError, SourceNotFoundError):
                # Non-retryable errors
                raise

        # All retries exhausted
        logger.error("All %d attempts failed for %s", self._config.max_retries, url)
        if last_exception:
            raise last_exception
        raise FetchError(
            f"Failed to fetch {url} after {self._config.max_retries} attempts"
        )

    def _should_retry(self, attempt: int) -> bool:
        """Determine if a retry should be attempted.

        Args:
            attempt: The current attempt number (1-based).

        Returns:
            True if another retry should be attempted, False otherwise.
        """
        return attempt < self._config.max_retries

    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate the delay before the next retry attempt.

        This implements an exponential backoff strategy.

        Args:
            attempt: The current attempt number (1-based).

        Returns:
            The delay in seconds before the next retry.
        """
        delay = self._config.retry_delay * (2**attempt)
        return min(delay, self._config.max_retry_delay)

    def _make_request(self, url: str, **kwargs) -> requests.Response:
        """Make an HTTP request to the specified URL.

        This method makes an HTTP GET request to the specified URL using the
        session, handles timeouts and connection errors, and validates the response.

        Args:
            url: The URL to request.
            **kwargs: Additional keyword arguments to pass to requests.get().

        Returns:
            The HTTP response.

        Raises:
            CrawlerConfigurationError: If the HTTP session is not initialized.
            FetchTimeoutError: If the request times out.
            FetchConnectionError: If there's a connection error.
            FetchError: For another request exception.
            Various HTTP errors from _validate_response.
        """
        if not self._session:
            raise CrawlerConfigurationError(
                issue="HTTP session not initialized",
                component="session",
            )

        try:
            response = self._session.get(
                url,
                timeout=self._config.req_timeout,
                **kwargs,
            )
            self._validate_response(url, response)
            return response

        except Timeout as exc:
            logger.error(
                "Request timeout for %s after %ds",
                url,
                self._config.req_timeout,
            )
            raise FetchTimeoutError(url, self._config.req_timeout) from exc

        except ConnectionError as exc:
            logger.error("Connection error for %s: %s", url, exc)
            raise FetchConnectionError(url, str(exc)) from exc

        except RequestException as exc:
            logger.error("Request error for %s: %s", url, exc)
            raise FetchError(f"Request failed for {url}: {exc}") from exc

    def _validate_response(self, url: str, response: requests.Response) -> None:
        """Validate an HTTP response and raise appropriate exceptions for errors.

        This method checks the HTTP status code and raises appropriate exceptions
        for different types of errors.

        Args:
            url: The URL that was requested.
            response: The HTTP response to validate.

        Raises:
            RateLimitError: If the server indicates rate limiting (429).
            SourceNotFoundError: If the resource is not found (404).
            FetchHTTPError: For other HTTP errors.
        """
        status_handlers = {
            HTTPStatusCode.TOO_MANY_REQUESTS: self._handle_rate_limit,
            HTTPStatusCode.NOT_FOUND: lambda u, r: SourceNotFoundError(u),
            HTTPStatusCode.FORBIDDEN: lambda u, r: FetchHTTPError(
                u,
                r.status_code,
                "Access forbidden",
            ),
            HTTPStatusCode.UNAUTHORIZED: lambda u, r: FetchHTTPError(
                u,
                r.status_code,
                "Authentication required",
            ),
            HTTPStatusCode.SERVICE_UNAVAILABLE: lambda u, r: FetchHTTPError(
                u,
                r.status_code,
                "Service unavailable",
            ),
        }

        if response.status_code in status_handlers:
            exception = status_handlers[response.status_code](url, response)
            logger.warning("HTTP error %d for %s", response.status_code, url)
            raise exception

        elif response.status_code >= HTTPStatusCode.INTERNAL_SERVER_ERROR:
            logger.warning("Server error %d for %s", response.status_code, url)
            raise FetchHTTPError(
                url, response.status_code, response.reason or "Server error"
            )

        elif response.status_code >= HTTPStatusCode.BAD_REQUEST:
            logger.warning("Client error %d for %s", response.status_code, url)
            raise FetchHTTPError(
                url, response.status_code, response.reason or "Client error"
            )

    def _handle_rate_limit(
        self,
        url: str,
        response: requests.Response,
    ) -> RateLimitError:
        """Handle a rate limit response (HTTP 429).

        This method extracts the Retry-After header from the response and creates
        a RateLimitError with the appropriate retry time.

        Args:
            url: The URL that was requested.
            response: The HTTP response with the rate limit error.

        Returns:
            A RateLimitError with the retry-after time if available.
        """
        retry_after_header = response.headers.get("Retry-After")
        retry_after = _parse_retry_after(retry_after_header)
        logger.warning("Rate limit exceeded for %s, retry after: %s", url, retry_after)
        return RateLimitError(url, retry_after)

    def _log_response_info(self, url: str, response: requests.Response) -> None:
        """Log information about an HTTP response.

        This method logs different information based on the response status code:
        - For successful responses (2xx): status code and content size
        - For redirects (3xx): status code and redirect location
        - For error responses (4xx, 5xx): status code and content size

        Args:
            url: The URL that was requested.
            response: The HTTP response to log information about.
        """
        try:
            content_size = humanize_filesize(len(response.content))
            status = response.status_code

            if status < 300:
                logger.debug(
                    "Response received from %s (status=%d, size=%s)",
                    url,
                    status,
                    content_size,
                )
            elif status < 400:
                location = response.headers.get("Location", "unknown")
                logger.debug(
                    "Redirect response received from %s (status=%d, location=%s)",
                    url,
                    status,
                    location,
                )
            else:
                logger.debug(
                    "Error response received from %s (status=%d, size=%s)",
                    url,
                    status,
                    content_size,
                )

        except Exception as exc:
            logger.debug("Failed to log response info for %s: %s", url, exc)

    def _setup_session(self) -> None:
        """Set up the HTTP session with the appropriate configuration.

        This method initializes the requests Session object with connection pooling,
        adapters for HTTP and HTTPS, and default headers.

        Raises:
            CrawlerConfigurationError: If the session setup fails.
        """
        try:
            self._session = requests.Session()

            adapter = requests.adapters.HTTPAdapter(
                pool_connections=self._config.pool_conn,
                pool_maxsize=self._config.pool_max_size,
                max_retries=0,  # We handle retries ourselves
            )

            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)

            # Set default headers
            self._session.headers.update(
                {
                    "Accept": (
                        "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                    ),
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                }
            )

        except Exception as exc:
            raise CrawlerConfigurationError(
                issue=f"Failed to setup HTTP session: {exc}",
                component="session_setup",
            ) from exc

    def _get_random_user_agent(self) -> str:
        """Get a random user agent string from the configured list.

        This method selects a random user agent from the configured list
        or returns a default user agent if the list is empty or selection fails.

        Returns:
            A user agent string.
        """
        if not self._config.user_agents:
            return "Mozilla/5.0 (compatible; BriefEx Crawler/1.0)"

        try:
            return random.choice(self._config.user_agents)
        except Exception as exc:
            logger.warning("Failed to select random user agent: %s", exc)
            return self._config.user_agents[0]

    @override
    def close(self) -> None:
        """Close the fetcher and release any resources.

        This method closes the HTTP session and releases any resources.
        It should be called when the fetcher is no longer needed.
        """
        if self._session:
            try:
                self._session.close()
                logger.debug("HTTP session closed")
            except Exception as exc:
                logger.error("Error closing HTTP session: %s", exc)
            finally:
                self._session = None
