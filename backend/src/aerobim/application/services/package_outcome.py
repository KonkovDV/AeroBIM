"""Single owner for package-level Shared-gate outcome (ADR-001)."""

from __future__ import annotations

from aerobim.application.services.capability_policy import (
    SignOffCapabilityPolicy,
    build_signoff_policy,
)
from aerobim.domain.models import ReportCapabilities
from aerobim.domain.package_outcome import PackageOutcome


def compute_package_outcome(
    *,
    error_count: int,
    warning_count: int,
    capabilities: ReportCapabilities | None,
    intake_blocked: bool,
    hitl_requires_review: bool = False,
    hard_clash_blocks: bool = False,
    policy: SignOffCapabilityPolicy | None = None,
) -> PackageOutcome:
    """Compute package outcome from deterministic inputs + sign-off policy.

    Precedence (ADR-001 / claim matrix):
    1. intake blocked or required capability not OK → BLOCKED
    2. executed finding failures / hard clashes → FAILED
    3. HITL review required → REVIEW_REQUIRED
    4. warnings only → PASS_WITH_WARNINGS
    5. else PASS
    """

    active = policy or build_signoff_policy(profile="development")
    capability_blocked = False
    if capabilities is not None:
        # Capability-side blocks as if finding error_count were zero.
        capability_blocked = not active.summary_passed(
            error_count=0,
            capabilities=capabilities,
        )

    if intake_blocked or capability_blocked:
        return PackageOutcome.BLOCKED
    if error_count > 0 or hard_clash_blocks:
        return PackageOutcome.FAILED
    if hitl_requires_review:
        return PackageOutcome.REVIEW_REQUIRED
    if warning_count > 0:
        return PackageOutcome.PASS_WITH_WARNINGS
    return PackageOutcome.PASS
