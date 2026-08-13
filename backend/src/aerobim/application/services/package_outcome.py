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

    Precedence (violation > missing data > uncertainty > compliance), matching
    the four-state contract in Mushkani et al., arXiv:2607.29058:

    1. confirmed finding failures / hard clashes → FAILED
    2. intake blocked or required capability not OK → BLOCKED
    3. HITL / missing source / low confidence → REVIEW_REQUIRED
    4. warnings only → PASS_WITH_WARNINGS
    5. else PASS

    REVIEW_REQUIRED never rewrites a violation into a pass. Incomplete evidence
    never becomes PASS.
    """

    active = policy or build_signoff_policy(profile="development")
    capability_blocked = False
    if capabilities is not None:
        # Capability-side blocks as if finding error_count were zero.
        capability_blocked = not active.summary_passed(
            error_count=0,
            capabilities=capabilities,
        )

    if error_count > 0 or hard_clash_blocks:
        return PackageOutcome.FAILED
    if intake_blocked or capability_blocked:
        return PackageOutcome.BLOCKED
    if hitl_requires_review:
        return PackageOutcome.REVIEW_REQUIRED
    if warning_count > 0:
        return PackageOutcome.PASS_WITH_WARNINGS
    return PackageOutcome.PASS
