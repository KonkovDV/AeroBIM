"""Object-level ACL helpers for report artifacts and async jobs (RT-005 / Phase 8)."""

from __future__ import annotations

from dataclasses import dataclass, field

from aerobim.domain.auth_roles import (
    HITL_REVIEWER_ROLES,
    NORM_PACK_EDITOR_ROLES,
    principal_has_any_role,
)
from aerobim.domain.models import AnalyzeProjectPackageJob, ValidationReport


@dataclass(frozen=True)
class AuthPrincipal:
    """Authenticated caller identity for object ACL checks."""

    tenant_id: str | None = None
    """Bound tenant; None means unrestricted (dev / ACL off)."""
    subject: str | None = None
    is_service_token: bool = False
    """True for static shared bearer — may be blocked from expert HITL writes."""
    roles: frozenset[str] = field(default_factory=frozenset)
    """Normalized role names from OIDC claims (casefold)."""


HITL_EXPERT_EVENT_TYPES = frozenset({"accepted", "rejected", "edited", "edited_remark", "waived"})


def principal_may_append_hitl_event(
    *,
    enforce_hitl_reviewer_auth: bool,
    require_hitl_reviewer_roles: bool,
    principal: AuthPrincipal,
    event_type: str,
) -> bool:
    """Gate expert HITL writes: shared static bearer never signs.

    Expert events (accept/reject/edit/waive) require a non-service principal.
    Under pilot/production profiles, reviewer/admin roles are also required.
    """

    if event_type not in HITL_EXPERT_EVENT_TYPES:
        return True
    # Shared API bearer has no expert identity — never a legal acceptance actor.
    if principal.is_service_token:
        return False
    if not enforce_hitl_reviewer_auth:
        return True
    if require_hitl_reviewer_roles:
        return principal_has_any_role(
            principal_roles=principal.roles,
            required=HITL_REVIEWER_ROLES,
        )
    return True


def principal_may_edit_norm_pack(
    *,
    enforce_rbac: bool,
    principal: AuthPrincipal,
) -> bool:
    """Gate norm-pack mutations on editor/reviewer/admin roles."""

    if not enforce_rbac:
        return True
    if principal.is_service_token:
        return False
    return principal_has_any_role(
        principal_roles=principal.roles,
        required=NORM_PACK_EDITOR_ROLES,
    )


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


def principal_may_access_norm_pack(
    *,
    enforce_object_acl: bool,
    principal: AuthPrincipal,
    tenant_id: str | None,
) -> bool:
    """Return False when enforced ACL denies cross-tenant norm-pack access."""

    if not enforce_object_acl:
        return True
    pack_tenant = (tenant_id or "").strip()
    if not pack_tenant:
        return False
    return _tenants_match(principal.tenant_id, pack_tenant)


__all__ = [
    "AuthPrincipal",
    "HITL_EXPERT_EVENT_TYPES",
    "principal_may_access_job",
    "principal_may_access_norm_pack",
    "principal_may_access_report",
    "principal_may_append_hitl_event",
    "principal_may_edit_norm_pack",
]
