import logging
import random
import time
from typing import override
from urllib.parse import urlparse

import requests
import requests.adapters
from pydantic import BaseModel
from requests.exceptions import ConnectionError, RequestException, Timeout

import utils

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
from .base import Fetcher
from .registry import register

logger = logging.getLogger(__name__)


class HTTPStatusCode:
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
    user_agents: list[str]
    request_timeout: int
    pool_connections: int
    pool_maxsize: int
    max_retries: int
    retry_delay: float
    max_retry_delay: float


DEFAULT_CONFIG = Config(
    user_agents=[
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Edge/120.0.2210.91 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    ],
    request_timeout=30,
    pool_connections=100,
    pool_maxsize=100,
    max_retries=3,
    retry_delay=1.0,
    max_retry_delay=60,
)


def _build_config(kwargs: dict) -> Config:
    try:
        return Config(
            user_agents=kwargs.get("user_agents", DEFAULT_CONFIG.user_agents),
            request_timeout=kwargs.get(
                "request_timeout",
                DEFAULT_CONFIG.request_timeout,
            ),
            pool_connections=kwargs.get(
                "pool_connections",
                DEFAULT_CONFIG.pool_connections,
            ),
            pool_maxsize=kwargs.get("pool_maxsize", DEFAULT_CONFIG.pool_maxsize),
            max_retries=kwargs.get("max_retries", DEFAULT_CONFIG.max_retries),
            retry_delay=kwargs.get("retry_delay", DEFAULT_CONFIG.retry_delay),
            max_retry_delay=kwargs.get(
                "max_retry_delay",
                DEFAULT_CONFIG.max_retry_delay,
            ),
        )
    except Exception as exc:
        raise CrawlerConfigurationError(
            issue=f"Invalid configuration parameters: {exc}",
            component="fetcher_configuration",
        ) from exc


def _validate_url(url: str) -> None:
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
    if not retry_after:
        return None

    try:
        return int(retry_after)
    except ValueError:
        logger.debug("Invalid Retry-After header value: %s", retry_after)
        return None


@register(SourceType.HTML)
class HTMLFetcher(Fetcher):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._session: requests.Session | None = None
        self._config = _build_config(kwargs)
        self._setup_session()

    @override
    def fetch(self, url: str) -> bytes:
        logger.info("Fetching HTML content from %s", url)
        _validate_url(url)
        headers = {"User-Agent": self._get_random_user_agent()}
        return self._fetch_with_retries(url, headers)

    def _fetch_with_retries(self, url: str, headers: dict[str, str]) -> bytes:
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
        return attempt < self._config.max_retries

    def _calculate_retry_delay(self, attempt: int) -> float:
        delay = self._config.retry_delay * (2**attempt)
        return min(delay, self._config.max_retry_delay)

    def _make_request(self, url: str, **kwargs) -> requests.Response:
        if not self._session:
            raise CrawlerConfigurationError(
                issue="HTTP session not initialized",
                component="session",
            )

        try:
            response = self._session.get(
                url,
                timeout=self._config.request_timeout,
                **kwargs,
            )
            self._validate_response(url, response)
            return response

        except Timeout as exc:
            logger.error(
                "Request timeout for %s after %ds",
                url,
                self._config.request_timeout,
            )
            raise FetchTimeoutError(url, self._config.request_timeout) from exc

        except ConnectionError as exc:
            logger.error("Connection error for %s: %s", url, exc)
            raise FetchConnectionError(url, str(exc)) from exc

        except RequestException as exc:
            logger.error("Request error for %s: %s", url, exc)
            raise FetchError(f"Request failed for {url}: {exc}") from exc

    def _validate_response(self, url: str, response: requests.Response) -> None:
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

    @staticmethod
    def _handle_rate_limit(url: str, response: requests.Response) -> RateLimitError:
        retry_after_header = response.headers.get("Retry-After")
        retry_after = _parse_retry_after(retry_after_header)
        logger.warning("Rate limit exceeded for %s, retry after: %s", url, retry_after)
        return RateLimitError(url, retry_after)

    @staticmethod
    def _log_response_info(url: str, response: requests.Response) -> None:
        try:
            content_size = utils.pretty_print_size(len(response.content))
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
        try:
            self._session = requests.Session()

            adapter = requests.adapters.HTTPAdapter(
                pool_connections=self._config.pool_connections,
                pool_maxsize=self._config.pool_maxsize,
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
        if not self._config.user_agents:
            return "Mozilla/5.0 (compatible; BriefEx Crawler/1.0)"

        try:
            return random.choice(self._config.user_agents)
        except Exception as exc:
            logger.warning("Failed to select random user agent: %s", exc)
            return self._config.user_agents[0]

    def close(self) -> None:
        if self._session:
            try:
                self._session.close()
                logger.debug("HTTP session closed")
            except Exception as exc:
                logger.error("Error closing HTTP session: %s", exc)
            finally:
                self._session = None
