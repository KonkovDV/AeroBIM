"""Sign-off helpers: capability failures must not look like a clean pass.

Canonical policy object lives in ``capability_policy.SignOffCapabilityPolicy``.
These module-level helpers remain for backward-compatible unit tests and call sites
that do not yet thread a full policy instance.
"""

from __future__ import annotations

from aerobim.application.services.capability_policy import (
    SignOffCapabilityPolicy,
    build_signoff_policy,
)
from aerobim.domain.models import CapabilityState, ReportCapabilities

# Re-export for discoverability / mutation tests.
_PASS_BLOCKING_CAPABILITY_FIELDS: tuple[str, ...] = (
    "clash",
    "ids",
    "ifc_validation",
    "unit_scale",
    "raster",
    "ifc_schema",
    "norm_rule_packs",
    "section_pairing",
    "calculation_match",
    "dwg_dxf",
    "mep_system_clash",
    "quantity",
)


def failed_capabilities_blocking_pass(capabilities: ReportCapabilities) -> tuple[str, ...]:
    """Return capability names in FAILED state that must force ``summary.passed=false``."""
    return build_signoff_policy(profile="development").failed_capabilities_blocking_pass(
        capabilities
    )


def summary_passed_after_capabilities(
    *,
    error_count: int,
    capabilities: ReportCapabilities,
    policy: SignOffCapabilityPolicy | None = None,
    require_mep_system_clash: bool = False,
) -> bool:
    """Compute report pass flag: zero ERROR issues and no FAILED capabilities.

    RT-SIGNOFF-002: ``calculation_match=NOT_VERIFIED`` must not green-pass.
    RT-HYPER-001: when ``require_mep_system_clash`` (or policy flag) is set,
    MEP NOT_VERIFIED/FAILED/SKIPPED/MISSING blocks pass — only OK is acceptable.
    """

    active = policy or build_signoff_policy(
        profile="development",
        require_mep_system_clash=require_mep_system_clash,
    )
    if policy is None and require_mep_system_clash:
        active = build_signoff_policy(
            profile="development",
            require_mep_system_clash=True,
        )
    return active.summary_passed(error_count=error_count, capabilities=capabilities)


# Keep CapabilityState import used (mutation / honesty guard).
_ = CapabilityState
