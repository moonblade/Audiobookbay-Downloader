"""Server-side fetch for remote cover art.

AudiobookBay poster URLs frequently cannot be loaded by the browser directly:
they are often plain http (blocked as mixed content on an https deployment),
and the hosts commonly refuse hotlinked requests based on the Referer header.
Fetching them here sidesteps both.

Proxying a URL supplied by the page is an SSRF primitive, so every request is
validated against the checks below before any connection is made. The app
usually sits on a Docker network alongside Jackett, qBittorrent and
FlareSolverr, all of which would otherwise be reachable through this endpoint.
"""
import ipaddress
import socket
from typing import Tuple
from urllib.parse import urlparse

import requests

from .jackett_urls import is_jackett_url, with_apikey
from .utils import custom_logger

logger = custom_logger(__name__)

FETCH_TIMEOUT: Tuple[int, int] = (5, 15)
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_REDIRECTS = 3


class UnsafeImageURL(Exception):
    """Raised when a URL fails validation and must not be fetched."""


def _assert_public_host(hostname: str) -> None:
    """Reject hosts that resolve to any non-public address.

    Every resolved address is checked, not just the first: a hostname can
    return both a public and a private record, and picking one would leave a
    trivial bypass.
    """
    if not hostname:
        raise UnsafeImageURL("missing hostname")

    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise UnsafeImageURL(f"cannot resolve host: {exc}")

    for info in infos:
        addr = ipaddress.ip_address(info[4][0])
        if (
            addr.is_private
            or addr.is_loopback
            or addr.is_link_local
            or addr.is_reserved
            or addr.is_multicast
            or addr.is_unspecified
        ):
            raise UnsafeImageURL(f"host resolves to non-public address {addr}")


def _validate(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UnsafeImageURL(f"unsupported scheme: {parsed.scheme!r}")
    # The configured Jackett host is trusted by definition -- it is where our
    # searches already go. Everything else must be publicly routable, so a
    # hostile poster URL cannot be used to reach other services on the network.
    if is_jackett_url(url):
        return
    _assert_public_host(parsed.hostname or "")


def fetch_image(url: str) -> Tuple[bytes, str]:
    """Fetch a remote image, returning (body, content_type).

    Redirects are followed manually so each hop is re-validated; letting
    requests follow them would allow a public URL to bounce to an internal one.
    """
    for _ in range(MAX_REDIRECTS + 1):
        _validate(url)
        if is_jackett_url(url):
            url = with_apikey(url)

        response = requests.get(
            url,
            timeout=FETCH_TIMEOUT,
            stream=True,
            allow_redirects=False,
            # Some hosts serve a placeholder unless a browser-ish UA is sent.
            headers={"User-Agent": "Mozilla/5.0", "Accept": "image/*,*/*"},
        )

        if response.status_code in (301, 302, 303, 307, 308):
            location = response.headers.get("Location")
            response.close()
            if not location:
                raise UnsafeImageURL("redirect without Location header")
            url = requests.compat.urljoin(url, location)
            continue

        if response.status_code != 200:
            response.close()
            raise UnsafeImageURL(f"upstream returned {response.status_code}")

        content_type = (response.headers.get("Content-Type") or "").split(";")[0].strip()
        if not content_type.startswith("image/"):
            response.close()
            raise UnsafeImageURL(f"not an image: {content_type!r}")

        # Read with a cap rather than trusting Content-Length, which a hostile
        # or broken host may understate.
        chunks, total = [], 0
        for chunk in response.iter_content(64 * 1024):
            total += len(chunk)
            if total > MAX_IMAGE_BYTES:
                response.close()
                raise UnsafeImageURL("image exceeds size limit")
            chunks.append(chunk)
        response.close()

        return b"".join(chunks), content_type

    raise UnsafeImageURL("too many redirects")
