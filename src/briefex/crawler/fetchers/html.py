from __future__ import annotations

import logging
import random
import time
import urllib.parse
from typing import Any, override

import requests
import requests.adapters

from briefex.crawler.exceptions import (
    FetchConnectionError,
    FetchError,
    FetchHttpError,
    FetchTimeoutError,
)
from briefex.crawler.fetchers import utils
from briefex.crawler.fetchers.base import Fetcher
from briefex.crawler.fetchers.registry import register

_log = logging.getLogger(__name__)

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Edge/120.0.2210.91 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

DEFAULT_SESSION_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

HTTP_STATUS_FORCE_LIST = [
    requests.codes.too_many_requests,
    requests.codes.internal_server_error,
    requests.codes.not_implemented,
    requests.codes.bad_gateway,
    requests.codes.service_unavailable,
    requests.codes.gateway_timeout,
]


@register("HTML")
class HTMLFetcher(Fetcher):
    """Fetcher for HTML content with retry and per-host session management."""

    def __init__(
        self,
        *,
        user_agents: list[str] | None = None,
        request_timeout: float,
        pool_connections: int,
        pool_maxsize: int,
        max_retries: int,
        retry_delay: float,
        max_retry_delay: float,
        **kwargs: Any,
    ) -> None:
        kwargs.update(
            {
                "user_agents": user_agents,
                "request_timeout": request_timeout,
                "pool_connections": pool_connections,
                "pool_maxsize": pool_maxsize,
                "max_retries": max_retries,
                "retry_delay": retry_delay,
                "max_retry_delay": max_retry_delay,
            }
        )
        super().__init__(*[], **kwargs)
        self._sessions_for_netloc: dict[str, requests.Session] = {}
        self._user_agents: list[str] = user_agents or DEFAULT_USER_AGENTS
        self._request_timeout = request_timeout
        self._pool_connections = pool_connections
        self._pool_maxsize = pool_maxsize
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._max_retry_delay = max_retry_delay

    @override
    def fetch(self, url: str, **kwargs: Any) -> bytes:
        """Fetch HTML bytes from the given URL, retrying on transient errors.

        Args:
            url: URL to retrieve.
        Returns:
            Response body as raw bytes.
        Raises:
            FetchTimeoutError: on timeout.
            FetchConnectionError: on connection failure.
            FetchHttpError: on HTTP status error.
            FetchError: on other fetch failures after retries.
        """
        utils.validate_url(url)
        _log.info("Starting fetch of HTML from URL '%s'", url)

        attempt = 0
        resp: requests.Response | None = None

        while True:
            is_last = attempt >= self._max_retries

            try:
                resp = self._send_request(url, **kwargs)
            except (FetchTimeoutError, FetchConnectionError, FetchError) as exc:
                if is_last:
                    _log.error(
                        "Fetch failed for URL '%s' after %d attempts: %s",
                        url,
                        attempt + 1,
                        exc,
                    )
                    raise
                _log.warning(
                    "Transient error on attempt %d for URL '%s': %s",
                    attempt + 1,
                    url,
                    exc,
                )
            else:
                status = resp.status_code
                if status not in HTTP_STATUS_FORCE_LIST or is_last:
                    try:
                        resp.raise_for_status()
                        _log.info(
                            "Fetched HTML from '%s' successfully "
                            "(status=%d, attempts=%d)",
                            url,
                            status,
                            attempt + 1,
                        )
                        return resp.content
                    except requests.HTTPError as exc:
                        _log.error(
                            "HTTP error fetching '%s' (status=%d): %s",
                            url,
                            status,
                            exc,
                        )
                        raise FetchHttpError(
                            issue=f"HTTP {status} error for URL '{url}': {exc}",
                            src_url=url,
                            status_code=status,
                        ) from exc

            if not is_last:
                delay = self._get_backoff(resp, attempt)
                _log.debug(
                    "Waiting %.2f seconds before retry %d for URL '%s'",
                    delay,
                    attempt + 2,
                    url,
                )
                time.sleep(delay)
                attempt += 1
                continue

        retries = self._max_retries + 1
        raise FetchError(
            message=f"Failed to fetch HTML from '{url}' after {retries} attempts."
        )

    @override
    def close(self) -> None:
        """Close all active HTTP sessions."""
        _log.debug("Closing all HTTP sessions (%d)", len(self._sessions_for_netloc))
        for netloc, session in self._sessions_for_netloc.items():
            _log.debug("Closing session for host '%s'", netloc)
            session.close()

    @property
    def _user_agent(self):
        ua = random.choice(self._user_agents)
        _log.debug("Selected User-Agent: %s", ua)
        return ua

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers["User-Agent"] = self._user_agent
        session.headers.update(DEFAULT_SESSION_HEADERS)

        adapter = requests.adapters.HTTPAdapter(
            pool_connections=self._pool_connections,
            pool_maxsize=self._pool_maxsize,
            max_retries=0,  # We handle retries ourselves
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        _log.debug(
            "Created new HTTP session (pool_connections=%d, pool_maxsize=%d)",
            self._pool_connections,
            self._pool_maxsize,
        )
        return session

    def _get_session(self, url: str | None = None) -> requests.Session:
        if not url:
            _log.debug("No URL provided; creating temporary session")
            return self._create_session()

        netloc = urllib.parse.urlsplit(url).netloc
        if netloc not in self._sessions_for_netloc:
            _log.info("Opening new session for host '%s'", netloc)
            self._sessions_for_netloc[netloc] = self._create_session()

        return self._sessions_for_netloc[netloc]

    def _send_request(self, url: str, **kwargs: Any) -> requests.Response:
        try:
            request = requests.Request("GET", url)
            session = self._get_session(url)
            prepared_request = session.prepare_request(request)
            return session.send(prepared_request, timeout=self._request_timeout)

        except requests.exceptions.Timeout as exc:
            _log.warning(
                "Request timeout after %.2f seconds for URL '%s'",
                self._request_timeout,
                url,
            )
            raise FetchTimeoutError(
                src_url=url,
                timeout=self._request_timeout,
            ) from exc

        except requests.exceptions.ConnectionError as exc:
            _log.warning("Connection error for URL '%s': %s", url, exc)
            raise FetchConnectionError(
                issue=str(exc),
                src_url=url,
            ) from exc

        except requests.exceptions.RequestException as exc:
            _log.error("RequestException for URL '%s': %s", url, exc)
            raise FetchError(
                message=str(exc),
                details={"src_url": url},
            ) from exc

    def _get_backoff(self, response: requests.Response | None, attempt: int) -> float:
        if response is not None:
            retry_after = response.headers.get("retry-after")
            if retry_after:
                delay = float(retry_after)
                _log.debug(
                    "Using 'Retry-After' header for backoff: %.2f seconds",
                    delay,
                )
                return delay

        delay = self._retry_delay * (2**attempt)
        delay = min(delay, self._max_retry_delay)

        _log.debug(
            "Calculated exponential backoff: %.2f seconds (attempt=%d)",
            delay,
            attempt + 1,
        )
        return delay
