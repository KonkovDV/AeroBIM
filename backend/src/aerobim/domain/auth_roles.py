"""OIDC role extraction and RBAC helpers (Wave 4)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

HITL_REVIEWER_ROLES = frozenset(
    {
        "reviewer",
        "hitl_reviewer",
        "aerobim:reviewer",
        "aerobim:hitl_reviewer",
        "admin",
        "aerobim:admin",
    }
)

NORM_PACK_EDITOR_ROLES = frozenset(
    {
        "norm_editor",
        "aerobim:norm_editor",
        "admin",
        "aerobim:admin",
        "reviewer",
        "aerobim:reviewer",
    }
)


def _normalize_role(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text.casefold() if text else None


def _walk_claim(claims: Mapping[str, Any], path: str) -> Any:
    current: Any = claims
    for part in path.split("."):
        if not isinstance(current, Mapping):
            return None
        current = current.get(part)
    return current


def extract_oidc_roles(claims: Mapping[str, Any], *, roles_claim: str) -> frozenset[str]:
    """Parse roles from flat list claim or dotted path (e.g. ``realm_access.roles``)."""

    claim_path = (roles_claim or "roles").strip() or "roles"
    raw = _walk_claim(claims, claim_path)
    if raw is None and claim_path != "roles":
        raw = claims.get("roles")
    if raw is None:
        realm = claims.get("realm_access")
        if isinstance(realm, Mapping):
            raw = realm.get("roles")
    roles: set[str] = set()
    if isinstance(raw, str):
        for piece in raw.replace(";", ",").split(","):
            norm = _normalize_role(piece)
            if norm:
                roles.add(norm)
    elif isinstance(raw, (list, tuple, set, frozenset)):
        for item in raw:
            norm = _normalize_role(item)
            if norm:
                roles.add(norm)
    return frozenset(roles)


def principal_has_any_role(*, principal_roles: frozenset[str], required: frozenset[str]) -> bool:
    if not required:
        return True
    if not principal_roles:
        return False
    lowered_required = {role.casefold() for role in required}
    return bool(principal_roles & lowered_required)


__all__ = [
    "HITL_REVIEWER_ROLES",
    "NORM_PACK_EDITOR_ROLES",
    "extract_oidc_roles",
    "principal_has_any_role",
]
