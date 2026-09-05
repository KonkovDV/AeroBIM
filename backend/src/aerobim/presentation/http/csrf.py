"""CSRF binding for BFF cookie mutations. Not production SSO.

Cookie auth (Phase 3 lab) plus SameSite=Lax is not enough on same-site
subdomains. A custom header forces a CORS preflight and cannot be set by a
plain HTML form. Bearer-only API clients without a BFF cookie are unchanged.
"""

from __future__ import annotations

from collections.abc import Mapping

from aerobim.infrastructure.auth.oidc_bff_phase3 import (
    HOST_SESSION_COOKIE_NAME,
    SESSION_COOKIE_NAME,
)

BFF_CSRF_HEADER = "X-AeroBIM-Requested-With"
BFF_CSRF_VALUE = "AeroBIMReviewShell"
_MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_SESSION_COOKIE_NAMES = (SESSION_COOKIE_NAME, HOST_SESSION_COOKIE_NAME)


def bff_session_cookie_present(cookies: Mapping[str, str]) -> bool:
    return any(bool(cookies.get(name)) for name in _SESSION_COOKIE_NAMES)


def mutating_bff_cookie_requires_csrf(*, method: str, cookies: Mapping[str, str]) -> bool:
    return method.upper() in _MUTATING_METHODS and bff_session_cookie_present(cookies)


def csrf_header_matches(header_value: str | None) -> bool:
    return (header_value or "").strip() == BFF_CSRF_VALUE


def csrf_request_headers() -> dict[str, str]:
    """Test/client helper. The value is public (custom-header CSRF), not a secret."""

    return {BFF_CSRF_HEADER: BFF_CSRF_VALUE}
