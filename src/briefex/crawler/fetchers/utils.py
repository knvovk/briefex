from __future__ import annotations

import urllib.parse

from briefex.crawler.exceptions import InvalidSourceError


def validate_url(url: str) -> None:
    if not url or not url.strip():
        raise InvalidSourceError(issue="URL cannot be empty")

    url = url.strip()
    parsed_url = urllib.parse.urlsplit(url)

    if parsed_url.scheme not in ("http", "https"):
        raise InvalidSourceError(
            issue="URL must use HTTP or HTTPS scheme",
            src_url=url,
        )

    if not parsed_url.netloc:
        raise InvalidSourceError(
            issue="URL must contain a valid domain",
            src_url=url,
        )

    invalid_chars = {" ", "\n", "\r", "\t"}
    if any(char in url for char in invalid_chars):
        raise InvalidSourceError(
            issue="URL contains invalid whitespace characters",
            src_url=url,
        )
