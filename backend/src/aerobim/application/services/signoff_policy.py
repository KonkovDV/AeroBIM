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
    # I0–I2 honesty fields: FAILED must not green-pass (Red Team RT-SIGNOFF-001)
    "calculation_match",
    "dwg_dxf",
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
    """Compute report pass flag: zero ERROR issues and no FAILED capabilities.

    RT-SIGNOFF-002: ``calculation_match=NOT_VERIFIED`` (source present but сверка
    not evaluated) must not green-pass. Other NOT_VERIFIED fields (e.g. DXF-only
    ``dwg_dxf``) remain non-blocking.
    """

    if error_count != 0:
        return False
    if failed_capabilities_blocking_pass(capabilities):
        return False
    calc = capabilities.calculation_match
    if calc is not None and calc.status is CapabilityState.NOT_VERIFIED:
        return False
    return True
