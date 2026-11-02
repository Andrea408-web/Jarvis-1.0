"""Small request-boundary checks for a loopback-only local control server."""
from __future__ import annotations

import hmac
import secrets
from urllib.parse import urlsplit


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_matches(candidate: str | None, expected: str) -> bool:
    return isinstance(candidate, str) and hmac.compare_digest(candidate.encode("utf-8"), expected.encode("utf-8"))


def validate_host(host: str | None, port: int) -> bool:
    """Reject DNS rebinding and arbitrary Host headers, including their ports."""
    if not isinstance(host, str):
        return False
    return host.lower() in {f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}"}


def validate_origin(origin: str | None, host: str) -> bool:
    """Only the exact same local origin may perform authenticated requests.

    Native clients can omit Origin and must still provide the CSRF token.
    Null origins and URLs containing paths or credentials never match.
    """
    if origin is None:
        return True
    if not isinstance(origin, str):
        return False
    try:
        parsed = urlsplit(origin)
        return (parsed.scheme == "http" and parsed.netloc.lower() == host.lower()
                and not parsed.username and not parsed.password
                and not parsed.path and not parsed.query and not parsed.fragment)
    except ValueError:
        return False
