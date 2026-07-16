"""Object-level ACL helpers for report artifacts (RT-005)."""

from __future__ import annotations

from dataclasses import dataclass

from aerobim.domain.models import ValidationReport


@dataclass(frozen=True)
class AuthPrincipal:
    """Authenticated caller identity for object ACL checks."""

    tenant_id: str | None = None
    """Bound tenant; None means unrestricted (dev / ACL off)."""
    subject: str | None = None


def principal_may_access_report(
    *,
    enforce_object_acl: bool,
    principal: AuthPrincipal,
    report: ValidationReport,
) -> bool:
    """Return False when enforced ACL denies cross-tenant artifact access."""

    if not enforce_object_acl:
        return True
    report_tenant = (report.tenant_id or "").strip()
    if not report_tenant:
        # Legacy reports without tenant binding are denied under enforced ACL.
        return False
    principal_tenant = (principal.tenant_id or "").strip()
    if not principal_tenant:
        return False
    return principal_tenant.casefold() == report_tenant.casefold()


__all__ = ["AuthPrincipal", "principal_may_access_report"]
