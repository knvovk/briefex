from __future__ import annotations

import logging
import re
import urllib.parse

from bs4 import Tag

from briefex.crawler.exceptions import ParseStructureError

_log = logging.getLogger(__name__)

NBSP_REGEX = re.compile(r"&nbsp;|\xa0")
WHITESPACE_REGEX = re.compile(r"\s+")


def find_required_tag(parent: Tag, name: str, cls: str, netloc: str) -> Tag:
    """Locate a child tag by name and class, raising if not found.

    Args:
        parent: Parent BeautifulSoup Tag to search within.
        name: Tag name to find.
        cls: CSS class to match.
        netloc: Source URL netloc for error context.

    Returns:
        The matching Tag.

    Raises:
        ParseStructureError: If parent is missing or tag is not found.
    """
    if not parent:
        raise ParseStructureError(
            issue=f"Parent tag '{name}' not found.",
            src_url=netloc,
        )

    tag = parent.find(name, class_=cls)
    if not tag:
        raise ParseStructureError(
            issue=f"Tag '{name}' not found.",
            src_url=netloc,
        )

    return tag


def find_required_attr(tag: Tag, name: str, netloc: str) -> str:
    """Retrieve a required attribute from a Tag, raising if missing.

    Args:
        tag: BeautifulSoup Tag to inspect.
        name: Attribute name to retrieve.
        netloc: Source URL netloc for error context.

    Returns:
        The attribute value.

    Raises:
        ParseStructureError: If tag is missing or attribute is not present.
    """
    if not tag:
        raise ParseStructureError(
            issue=f"Tag '{name}' not found.",
            src_url=netloc,
        )

    attr = tag.get(name)
    if not attr:
        raise ParseStructureError(
            issue=f"Attribute '{name}' not found.",
            src_url=netloc,
        )

    return attr


def clean_text(text: str | None) -> str:
    """Clean text by replacing non-breaking spaces and collapsing whitespace."""
    if not text:
        return ""

    cleaned = NBSP_REGEX.sub(" ", text)
    cleaned = WHITESPACE_REGEX.sub(" ", cleaned).strip()

    return cleaned


def netloc(url: str) -> str:
    """Extract the network location component from a URL."""
    parsed_url = urllib.parse.urlsplit(url)
    return parsed_url.netloc
