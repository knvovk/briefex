import logging
import random
import time
from typing import override

import requests
import requests.adapters
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout

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
from .base import BaseFetcher
from .factory import register

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Edge/120.0.2210.91 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]
DEFAULT_REQUEST_TIMEOUT = 30
DEFAULT_POOL_CONNECTIONS = 100
DEFAULT_POOL_MAXSIZE = 100
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0

MAX_RETRY_DELAY = 60.0

HTTP_SCHEMA = "http://"
HTTPS_SCHEMA = "https://"


@register(SourceType.HTML)
class HTMLFetcher(BaseFetcher):

    def __init__(self, *args, **kwargs) -> None:
        try:
            super().__init__(*args, **kwargs)
            self._session: requests.Session | None = None

            self._user_agents = kwargs.get("user_agents", DEFAULT_USER_AGENTS)
            self._request_timeout = kwargs.get("request_timeout", DEFAULT_REQUEST_TIMEOUT)
            self._pool_connections = kwargs.get("pool_connections", DEFAULT_POOL_CONNECTIONS)
            self._pool_maxsize = kwargs.get("pool_maxsize", DEFAULT_POOL_MAXSIZE)
            self._max_retries = kwargs.get("max_retries", DEFAULT_MAX_RETRIES)
            self._retry_delay = kwargs.get("retry_delay", DEFAULT_RETRY_DELAY)

            self._setup_session()

            logger.debug(
                "%s initialized with user_agents=%s, request_timeout=%d, "
                "pool_connections=%d, pool_maxsize=%d, max_retries=%d",
                self.__class__.__name__,
                self._user_agents,
                self._request_timeout,
                self._pool_connections,
                self._pool_maxsize,
                self._max_retries,
            )

        except Exception as exc:
            logger.error("Error initializing HTMLFetcher: %s", exc)
            raise CrawlerConfigurationError(
                issue=f"Error initializing HTMLFetcher: {exc}",
                component="fetcher_initialization",
            ) from exc

    @override
    def fetch(self, url: str) -> bytes:
        logger.info("Starting HTML fetch process for %s", url)
        self._validate_url(url)
        headers = {"User-Agent": self._get_random_user_agent()}
        return self._fetch_with_retries(url, headers)

    def _validate_url(self, url: str) -> None:
        if not url or not url.strip():
            raise InvalidSourceError("", "URL must be specified")

        url = url.strip()
        if not url.startswith((HTTP_SCHEMA, HTTPS_SCHEMA)):
            raise InvalidSourceError(url, "URL must start with http:// or https://")

        if any(char in url for char in [" ", "\n", "\r", "\t"]):
            raise InvalidSourceError(url, "URL must not contain spaces or newlines")

    def _fetch_with_retries(self, url: str, headers: dict) -> bytes:
        last_exc = None

        for attempt in range(self._max_retries + 1):
            try:
                logger.debug(
                    "Attempt %d/%d: initiating request to %s with headers=%s",
                    attempt + 1,
                    self._max_retries + 1,
                    url,
                    headers,
                )

                response = self._make_request(url, headers=headers)
                self._log_response_success(url, response)

                response.raise_for_status()

                logger.info(
                    "Successfully fetched response from %s (status=%s, attempts=%s)",
                    url,
                    response.status_code,
                    attempt,
                )
                return response.content

            except (FetchTimeoutError, FetchConnectionError) as exc:
                last_exc = exc
                if attempt < self._max_retries:
                    delay = min(self._retry_delay * (2**attempt), MAX_RETRY_DELAY)
                    logger.warning(
                        "Attempt %d failed for %s: %s. Retrying in %d seconds...",
                        attempt + 1,
                        url,
                        exc,
                        delay,
                    )
                    time.sleep(delay)
                    continue
                else:
                    logger.error("All %d attempts failed for %s: %s", self._max_retries, url, exc)
                    break

            except (RateLimitError, FetchHTTPError, SourceNotFoundError) as exc:
                logger.error("Non-retryable error for %s: %s", url, exc)
                raise exc

            except HTTPError as exc:
                status_code = exc.response.status_code if exc.response else 0

                if status_code == 404:
                    logger.error("Page Not Found error for %s: %s", url, exc)
                    raise SourceNotFoundError(url) from exc

                elif status_code == 403:
                    logger.error("Forbidden error for %s: %s", url, exc)
                    raise FetchHTTPError(url, status_code, "Forbidden") from exc

                elif status_code == 429:
                    retry_after = exc.response.headers.get("Retry-After")
                    retry_after_int = int(retry_after) if retry_after and retry_after.isdigit() else None
                    logger.error("Rate limit error for %s: %s", url, exc)
                    raise RateLimitError(url, retry_after_int) from exc

                else:
                    logger.error("HTTP error for %s: %s", url, exc)
                    raise FetchHTTPError(url, status_code, exc.response.reason or "HTTP Error") from exc

            except RequestException as exc:
                logger.error("Network or request error during request to %s: %s", url, exc)
                raise FetchError(f"Request error for URL {url}: {exc}") from exc

            except Exception as exc:
                logger.error("Unexpected error during request to %s: %s", url, str(exc))
                raise FetchError(f"Unexpected error for URL {url}: {exc}") from exc

        raise last_exc

    def _log_response_success(self, url: str, response: requests.Response) -> None:
        try:
            content_size = utils.pretty_print_size(len(response.content))

            if response.status_code < 300:
                logger.debug(
                    "Successfully received response from %s (status=%d, size=%s)",
                    url,
                    response.status_code,
                    content_size,
                )
            elif response.status_code < 400:
                logger.warning(
                    "Received redirect response from %s (status=%d, location=%s, size=%s)",
                    url,
                    response.status_code,
                    response.headers.get("Location", "unknown"),
                    content_size,
                )
            else:
                logger.warning(
                    "Received error response from %s (status=%d, size=%s)",
                    url,
                    response.status_code,
                    content_size,
                )
        except Exception as exc:
            logger.debug("Error logging response info for %s: %s", url, exc)

    def _setup_session(self) -> None:
        try:
            self._session = requests.Session()

            adapter = requests.adapters.HTTPAdapter(
                pool_connections=self._pool_connections,
                pool_maxsize=self._pool_maxsize,
                max_retries=self._max_retries,
            )

            self._session.mount(HTTP_SCHEMA, adapter)
            self._session.mount(HTTPS_SCHEMA, adapter)

            self._session.headers.update(
                {
                    # 'User-Agent': 'BriefEx Crawler/1.0',
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                }
            )

            logger.debug(
                "Session initialized with pool_connections=%d, pool_maxsize=%d",
                self._pool_connections,
                self._pool_maxsize,
            )
        except Exception as exc:
            logger.error("Error setting up session: %s", exc)
            raise CrawlerConfigurationError(
                issue=f"Error setting up session: {exc}",
                component="html_fetcher_session",
            ) from exc

    def _get_random_user_agent(self) -> str:
        try:
            user_agent = random.choice(self._user_agents)
            logger.debug("Selected random User-Agent: %s", user_agent)
            return user_agent
        except Exception as exc:
            logger.error("Error selecting random User-Agent: %s", exc)
            return "Mozilla/5.0 (compatible; BriefEx Crawler/1.0)"

    def _make_request(self, url: str, **kwargs) -> requests.Response:
        try:
            if not self._session:
                raise CrawlerConfigurationError(
                    issue="HTTP session is not initialized",
                    component="html_fetcher_session",
                )

            response = self._session.get(url, timeout=self._request_timeout, **kwargs)
            self._handle_response_errors(url, response)
            return response

        except Timeout as exc:
            logger.error(
                "Timeout error for URL %s after %d seconds: %s",
                url,
                self._request_timeout,
                exc,
            )
            raise FetchTimeoutError(url, self._request_timeout) from exc

        except ConnectionError as exc:
            logger.error("Connection error for URL %s: %s", url, exc)
            raise FetchConnectionError(url, str(exc)) from exc

        except RequestException as exc:
            logger.error("Request error for URL %s: %s", url, exc)
            raise FetchError(f"Request error for URL {url}: {exc}") from exc

        except Exception as exc:
            logger.error("Unexpected error making request to %s: %s", url, exc)
            raise FetchError(f"Unexpected error making request to {url}: {exc}")

    def _handle_response_errors(self, url: str, response: requests.Response) -> None:
        try:
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                retry_after_int = int(retry_after) if retry_after and retry_after.isdigit() else None
                logger.warning("Rate limit hit for %s, retry after: %s", url, retry_after)
                raise RateLimitError(url, retry_after_int)

            elif response.status_code == 404:
                logger.warning("Page not found: %s", url)
                raise SourceNotFoundError(url)

            elif response.status_code == 403:
                logger.warning("Access forbidden for %s", url)
                raise FetchHTTPError(url, 403, "Access forbidden")

            elif response.status_code == 401:
                logger.warning("Authentication required for %s", url)
                raise FetchHTTPError(url, 401, "Authentication required")

            elif response.status_code == 503:
                logger.warning("Service unavailable: %s", url)
                raise FetchHTTPError(url, 503, "Service unavailable")

            elif response.status_code >= 500:
                logger.warning("Server error for %s (status=%d)", url, response.status_code)
                raise FetchHTTPError(url, response.status_code, response.reason or "Server error")

            elif response.status_code >= 400:
                logger.warning("Client error for %s (status=%d)", url, response.status_code)
                raise FetchHTTPError(url, response.status_code, response.reason or "Client error")
        except (RateLimitError, FetchHTTPError, SourceNotFoundError):
            raise
        except Exception as exc:
            logger.error("Error handling response errors for %s: %s", url, exc)
            raise FetchError(f"Error handling response errors for {url}: {exc}") from exc

    def close(self) -> None:
        try:
            if self._session:
                self._session.close()
                self._session = None
                logger.debug("HTTP session closed.")
        except Exception as exc:
            logger.error("Error closing HTTP session: %s", exc)
            raise CrawlerConfigurationError(
                issue=f"Error closing HTTP session: {exc}",
                component="html_fetcher_session",
            ) from exc
