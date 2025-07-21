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
        super().__init__(
            user_agents,
            request_timeout,
            pool_connections,
            pool_maxsize,
            max_retries,
            retry_delay,
            max_retry_delay,
            **kwargs,
        )
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
        _log.info("Fetching HTML content from %s", url)
        utils.validate_url(url)

        attempt = 0
        resp = None

        while True:
            is_last_attempt = attempt >= self._max_retries

            try:
                resp = self._send_request(url, **kwargs)
            except (FetchTimeoutError, FetchConnectionError, FetchError) as exc:
                if is_last_attempt:
                    _log.error("Failed to fetch HTML content: %s", exc)
                    raise exc
            else:
                if resp.status_code not in HTTP_STATUS_FORCE_LIST or is_last_attempt:
                    try:
                        resp.raise_for_status()
                        _log.info(
                            "Successfully fetched %s (status=%d, attempt=%d)",
                            url,
                            resp.status_code,
                            attempt,
                        )
                        return resp.content
                    except requests.HTTPError as exc:
                        _log.error("Failed to fetch HTML content: %s", exc)
                        raise FetchHttpError(
                            issue=f"Failed to fetch HTML content: {exc}",
                            src_url=url,
                            status_code=resp.status_code,
                        ) from exc

            if not is_last_attempt:
                attempt += 1
                delay = self._get_backoff(resp, attempt)
                _log.debug("Retrying in %d seconds...", delay)
                time.sleep(delay)
                continue

        raise FetchError(
            f"Failed to fetch HTML content from {url} "
            f"after {self._max_retries} retries."
        )

    @override
    def close(self) -> None:
        """Close all active HTTP sessions."""
        for session in self._sessions_for_netloc.values():
            if session is not None:
                session.close()

    @property
    def _user_agent(self):
        return random.choice(self._user_agents)

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

        return session

    def _get_session(self, url: str | None = None) -> requests.Session:
        if not url:
            return self._create_session()

        parsed_url = urllib.parse.urlsplit(url)
        netloc = parsed_url.netloc

        if netloc not in self._sessions_for_netloc:
            _log.debug("Creating new session for %s", netloc)
            self._sessions_for_netloc[netloc] = self._create_session()

        return self._sessions_for_netloc[netloc]

    def _send_request(self, url: str, **kwargs: Any) -> requests.Response:
        try:
            request = requests.Request("GET", url)
            session = self._get_session(url)
            prepared_request = session.prepare_request(request)
            return session.send(prepared_request, timeout=self._request_timeout)

        except requests.exceptions.Timeout as exc:
            raise FetchTimeoutError(
                src_url=url,
                timeout=self._request_timeout,
            ) from exc

        except requests.exceptions.ConnectionError as exc:
            raise FetchConnectionError(
                issue=str(exc),
                src_url=url,
            ) from exc

        except requests.exceptions.RequestException as exc:
            raise FetchError(
                message=str(exc),
                details={
                    "src_url": url,
                },
            ) from exc

    def _get_backoff(self, response: requests.Response, attempt: int) -> float:
        if response is not None:
            retry_after = response.headers.get("retry-after", "")
            if retry_after:
                return float(retry_after)
        delay = self._retry_delay * (2**attempt)
        return min(delay, self._max_retry_delay)
