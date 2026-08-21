"""Search AudiobookBay through a configured Jackett indexer."""
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

from .constants import JACKETT_API_KEY, JACKETT_API_URL
from .utils import custom_logger

logger = custom_logger(__name__)

# (connect, read) budgets for outbound calls.
#
# Searching AudiobookBay is inherently slow: Jackett's indexer fetches a detail
# page per result, and when the site is behind a Cloudflare challenge Jackett
# solves it through FlareSolverr first. Ten-plus seconds is normal, so the read
# budget is deliberately generous.
#
# It must still exist, though. Without a timeout an unresponsive Jackett or
# FlareSolverr pins the worker thread handling the request forever, and the
# caller waits on a response that will never arrive.
REQUEST_TIMEOUT: Tuple[int, int] = (5, 120)
MAGNET_TIMEOUT: Tuple[int, int] = (5, 30)


def get_jackett_magnet(url: str) -> str:
    """Resolve a Jackett download link to the magnet URI it redirects to.

    Returns the input unchanged if it is already a magnet, or if resolution
    fails -- callers hand the result straight to a torrent client, which will
    surface the failure more usefully than an exception here would.
    """
    try:
        if url.startswith("magnet:"):
            return url
        response = requests.get(url, allow_redirects=False, timeout=MAGNET_TIMEOUT)
        if response.status_code in [301, 302]:
            return response.headers.get("Location", url)
    except Exception as e:
        logger.error(f"Error fetching magnet URL: {e}")
        return url
    return url


def search_audiobook(
    query: str,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Run a search against Jackett, returning its raw result dicts.

    Results are returned exactly as Jackett provides them, so callers see the
    full torznab field set (Title, Size, Seeders, Details, Poster, Link, ...).

    Jackett caches searches itself, so no caching is layered on here.
    """
    url = api_url or JACKETT_API_URL
    key = api_key or JACKETT_API_KEY

    # No Category parameter: the configured URL already scopes the search to
    # the audiobookbay indexer, and Jackett expects numeric torznab category
    # ids here rather than a name, so passing one had no effect.
    params = {"apikey": key, "Query": query}

    logger.info(f"Searching for {query!r}...")
    started = time.monotonic()
    response = requests.get(str(url), params=params, timeout=REQUEST_TIMEOUT)
    elapsed = time.monotonic() - started

    if response.status_code != 200:
        logger.error(f"Error fetching results from Jackett: {response.text}")
        return []

    results = response.json().get("Results", [])
    logger.info(f"Found {len(results)} results for {query!r} in {elapsed:.1f}s")
    return results
