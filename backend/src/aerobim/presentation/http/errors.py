"""Public HTTP error detail helpers (RT-ERR-001)."""

from __future__ import annotations

_PUBLIC_BAD_REQUEST = "Invalid request"
_PUBLIC_SERVICE_UNAVAILABLE = "Service unavailable"


def public_bad_request_detail() -> str:
    """Stable client-facing 400 detail — never echo internal ``ValueError`` text."""

    return _PUBLIC_BAD_REQUEST


def public_service_unavailable_detail() -> str:
    """Stable client-facing 503 detail."""

    return _PUBLIC_SERVICE_UNAVAILABLE


__all__ = [
    "public_bad_request_detail",
    "public_service_unavailable_detail",
]
