import logging
import random
from typing import override

import requests
import requests.adapters

import utils
from .base import BaseFetcher
from .factory import register
from ..models import SourceType

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Edge/120.0.2210.91 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

HTTP_SCHEMA = "http://"
HTTPS_SCHEMA = "https://"


@register(SourceType.HTML)
class HTMLFetcher(BaseFetcher):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._session: requests.Session | None = None
        self._user_agents = kwargs.get("user_agents", DEFAULT_USER_AGENTS)
        self._request_timeout = kwargs.get("request_timeout", 10)
        self._pool_connections = kwargs.get("pool_connections", 100)
        self._pool_maxsize = kwargs.get("pool_maxsize", 100)
        self._max_retries = kwargs.get("max_retries", 0)
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

    @override
    def fetch(self, url: str) -> bytes:
        logger.info("Starting HTML fetch process for %s", url)
        headers = {"User-Agent": self._get_random_user_agent()}
        try:
            session = self._get_session()
            logger.debug("Initiating request to %s with headers=%s", url, headers)
            response = session.get(url, headers=headers, timeout=self._request_timeout)
            if response.status_code < 400:
                logger.debug(
                    "Successfully received response from %s (status=%d, size=%s)",
                    url,
                    response.status_code,
                    utils.pretty_print_size(len(response.content)),
                )
                if response.status_code >= 300:
                    logger.warning(
                        "Received redirect response from %s (status=%d, location=%s)",
                        url,
                        response.status_code,
                        response.headers.get('Location', 'unknown'),
                    )
            else:
                logger.warning(
                    "Received error response from %s (status=%d)",
                    url,
                    response.status_code,
                )
            response.raise_for_status()
            logger.info("Fetched response from %s (status=%d)", url, response.status_code)
            return response.content
        except requests.HTTPError as exc:
            logger.error(
                "HTTP error during request to %s (status=%d, reason=%s)",
                url,
                exc.response.status_code,
                exc.response.reason,
            )
            raise
        except requests.RequestException as exc:
            logger.error(
                "Network or request error during request to %s: %s",
                url,
                str(exc),
            )
            raise
        except Exception as exc:
            logger.error(
                "Unexpected error during request to %s: %s",
                url,
                str(exc),
                exc_info=True,
            )
            raise

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=self._pool_connections,
                pool_maxsize=self._pool_maxsize,
                max_retries=self._max_retries,
            )
            self._session.mount(HTTP_SCHEMA, adapter)
            self._session.mount(HTTPS_SCHEMA, adapter)
            logger.debug(
                "Session initialized with pool_connections=%d, pool_maxsize=%d",
                self._pool_connections,
                self._pool_maxsize,
            )
        return self._session

    def _get_random_user_agent(self) -> str:
        user_agent = random.choice(self._user_agents)
        logger.debug("Selected random User-Agent: %s", user_agent)
        return user_agent
