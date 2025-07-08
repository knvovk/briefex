import uuid
from urllib.parse import urlparse


def normalize_id(raw_id: str, src_name: str) -> str:
    """Generate a normalized UUID for an entity based on its raw ID and source name.

    Args:
        raw_id: The original ID of the entity.
        src_name: The name of the source where the entity comes from.

    Returns:
        A normalized string representation of UUID5 generated from the combination
        of source name and raw ID.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{src_name}/{raw_id}"))


def humanize_time(seconds: float) -> str:
    """Convert seconds to a human-readable time format.

    Args:
        seconds: The time in seconds to be converted.

    Returns:
        A formatted string representing the time in the most appropriate unit:
        - milliseconds for times less than 1 second
        - seconds for times between 1 and 60 seconds
        - minutes and seconds for times greater than 60 seconds
    """
    if seconds < 1:
        return f"{seconds * 1000:.2f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        remaining = seconds % 60
        return f"{minutes}min {remaining:.2f}s"


def humanize_filesize(size_in_bytes: float) -> str:
    """Convert file size in bytes to a human-readable format.

    Args:
        size_in_bytes: The file size in bytes to be converted.

    Returns:
        A formatted string representing the file size with the most appropriate unit
        (B, kB, mB, gB). Sizes are displayed as integers for bytes and with two decimal
        places for larger units.
    """
    byte_unit_size = 1024
    units = ["B", "kB", "mB", "gB"]
    max_unit_index = len(units) - 1

    unit_idx = 0
    while size_in_bytes >= byte_unit_size and unit_idx < max_unit_index:
        size_in_bytes /= byte_unit_size
        unit_idx += 1

    if unit_idx == 0:
        return f"{int(size_in_bytes)} {units[unit_idx]}"

    return f"{size_in_bytes:.2f} {units[unit_idx]}"


def get_domain_from_url(url: str) -> str:
    """Extract the domain name from a URL.

    Args:
        url: The URL from which to extract the domain.

    Returns:
        The domain name (netloc) extracted from the URL, or an empty string if
        parsing fails.

    Note:
        If the URL doesn't start with 'http://' or 'https://', 'http://' will be
        prepended before parsing.
    """
    if not url.startswith(("http://", "https://")):
        url_to_parse = "https://" + url
    else:
        url_to_parse = url

    try:
        parsed_uri = urlparse(url_to_parse)
        return parsed_uri.netloc
    except Exception:
        return ""
