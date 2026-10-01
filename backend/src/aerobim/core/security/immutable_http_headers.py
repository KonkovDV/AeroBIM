"""Immutable outbound HTTP header merge (RT-20260811-01 / -06)."""

from __future__ import annotations

from collections.abc import Mapping

# Callers must never override these via extra_headers.
_IMMUTABLE_HEADER_NAMES = frozenset(
    {
        "authorization",
        "content-type",
        "accept",
        "host",
    }
)


def merge_outbound_headers(
    extra_headers: Mapping[str, str] | None,
    *,
    forced: Mapping[str, str],
    also_deny: frozenset[str] | None = None,
) -> dict[str, str]:
    """Merge optional extras then force security-critical headers last.

    Extra keys whose names (case-insensitive) are immutable — or listed in
    ``also_deny`` — are dropped so they cannot override ``forced``.
    """

    deny = _IMMUTABLE_HEADER_NAMES
    if also_deny:
        deny = deny | {name.lower() for name in also_deny}
    headers: dict[str, str] = {}
    for key, value in dict(extra_headers or {}).items():
        name = str(key)
        if name.lower() in deny:
            continue
        headers[name] = str(value)
    for key, value in forced.items():
        headers[str(key)] = str(value)
    return headers


__all__ = ["merge_outbound_headers"]
