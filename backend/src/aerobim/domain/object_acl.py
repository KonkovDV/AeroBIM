"""Object-level ACL helpers for report artifacts and async jobs (RT-005 / Phase 8)."""

from __future__ import annotations

from dataclasses import dataclass

from aerobim.domain.models import AnalyzeProjectPackageJob, ValidationReport


@dataclass(frozen=True)
class AuthPrincipal:
    """Authenticated caller identity for object ACL checks."""

    tenant_id: str | None = None
    """Bound tenant; None means unrestricted (dev / ACL off)."""
    subject: str | None = None


def _tenants_match(left: str | None, right: str | None) -> bool:
    a = (left or "").strip()
    b = (right or "").strip()
    if not a or not b:
        return False
    return a.casefold() == b.casefold()


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
    return _tenants_match(principal.tenant_id, report_tenant)


def principal_may_access_job(
    *,
    enforce_object_acl: bool,
    principal: AuthPrincipal,
    job: AnalyzeProjectPackageJob,
) -> bool:
    """Return False when enforced ACL denies cross-tenant job access/cancel."""

    if not enforce_object_acl:
        return True
    job_tenant = (job.tenant_id or "").strip()
    if not job_tenant:
        return False
    return _tenants_match(principal.tenant_id, job_tenant)


__all__ = [
    "AuthPrincipal",
    "principal_may_access_job",
    "principal_may_access_report",
]
