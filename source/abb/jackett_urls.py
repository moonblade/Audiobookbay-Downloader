"""Helpers for the Jackett URLs that appear inside search results.

Jackett embeds its API key in the URLs it hands back -- artwork (`Poster`) and
download links (`Link`, `BlackholeLink`). Those results are returned to the
browser, so the key would otherwise be readable by anyone who can see a search
response, a proxy log, or the devtools network tab, and it grants full access
to the Jackett API.

The key is therefore stripped on the way out and re-attached server-side at the
point of use. The browser only ever sees a keyless URL.
"""
from typing import Optional, Tuple
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse

from .config_db import get_effective_config

APIKEY_PARAM = "jackett_apikey"

# Result fields known to carry Jackett URLs with the key embedded.
URL_FIELDS = ("Poster", "Link", "BlackholeLink", "Details", "Guid")


def jackett_netloc() -> Optional[Tuple[str, Optional[int]]]:
    """(host, port) of the configured Jackett instance, or None."""
    api_url = get_effective_config("jackett_api_url") or ""
    parsed = urlparse(str(api_url))
    if not parsed.hostname:
        return None
    return parsed.hostname, parsed.port


def is_jackett_url(url: str) -> bool:
    """True when the URL points at the Jackett instance we are configured to use."""
    target = jackett_netloc()
    if target is None or not isinstance(url, str):
        return False
    parsed = urlparse(url)
    return (parsed.hostname, parsed.port) == target


def strip_apikey(url: str) -> str:
    """Remove the Jackett API key from a URL before it reaches the browser."""
    parsed = urlparse(url)
    params = [(k, v) for k, v in parse_qsl(parsed.query) if k != APIKEY_PARAM]
    return urlunparse(parsed._replace(query=urlencode(params)))


def with_apikey(url: str) -> str:
    """Re-attach the configured API key. No-op for non-Jackett URLs."""
    if not is_jackett_url(url):
        return url
    api_key = get_effective_config("jackett_api_key")
    if not api_key:
        return url
    parsed = urlparse(url)
    params = [(k, v) for k, v in parse_qsl(parsed.query) if k != APIKEY_PARAM]
    params.append((APIKEY_PARAM, str(api_key)))
    return urlunparse(parsed._replace(query=urlencode(params)))


def sanitize_result(result: dict) -> dict:
    """Copy a search result with the API key removed from every Jackett URL.

    Copied rather than mutated: the caller may be handing us the cached list,
    which other callers should not see rewritten underneath them.
    """
    replacements = {}
    for field in URL_FIELDS:
        value = result.get(field)
        if isinstance(value, str) and APIKEY_PARAM in value:
            replacements[field] = strip_apikey(value)
    return {**result, **replacements} if replacements else result
