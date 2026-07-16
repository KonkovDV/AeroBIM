"""Sign-off helpers: capability failures must not look like a clean pass."""

from __future__ import annotations

from aerobim.domain.models import CapabilityState, ReportCapabilities

# Capabilities that were attempted and FAILED block summary.passed.
# SKIPPED (not requested / optional extra missing) does not block.
_PASS_BLOCKING_CAPABILITY_FIELDS: tuple[str, ...] = (
    "clash",
    "ids",
    "ifc_validation",
    "unit_scale",
    "raster",
    "ifc_schema",
    "norm_rule_packs",
    "section_pairing",
)


def failed_capabilities_blocking_pass(capabilities: ReportCapabilities) -> tuple[str, ...]:
    """Return capability names in FAILED state that must force ``summary.passed=false``."""
    blocked: list[str] = []
    for name in _PASS_BLOCKING_CAPABILITY_FIELDS:
        status = getattr(capabilities, name, None)
        if status is not None and status.status is CapabilityState.FAILED:
            blocked.append(name)
    return tuple(blocked)


def summary_passed_after_capabilities(
    *,
    error_count: int,
    capabilities: ReportCapabilities,
) -> bool:
    """Compute report pass flag: zero ERROR issues and no FAILED capabilities."""
    if error_count != 0:
        return False
    return not failed_capabilities_blocking_pass(capabilities)
