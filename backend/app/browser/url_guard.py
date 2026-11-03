from urllib.parse import urlparse

ALLOWED_SCHEMES = {"http", "https"}
DEFAULT_PORTS = {"http": 80, "https": 443}


class BlockedURLError(Exception):
    """Raised when a URL is not on the approved target list."""


def _origin(url: str) -> tuple[str, str, int]:
    try:
        parsed = urlparse(url)
        scheme = (parsed.scheme or "").lower()
        if scheme not in ALLOWED_SCHEMES:
            raise BlockedURLError(f"Scheme not allowed: '{scheme or 'none'}'")
        if not parsed.hostname:
            raise BlockedURLError("URL has no host")
        port = parsed.port or DEFAULT_PORTS[scheme]
    except ValueError as exc:
        raise BlockedURLError(f"Malformed URL: {url}") from exc
    return scheme, parsed.hostname.lower(), port


def validate_url(url: str, allowed_origins: list[str]) -> str:
    """Return the URL if its origin is approved, otherwise raise BlockedURLError."""
    target = _origin(url)
    allowed = {_origin(o) for o in allowed_origins}
    if target not in allowed:
        raise BlockedURLError(f"Origin not approved: {url}")
    return url