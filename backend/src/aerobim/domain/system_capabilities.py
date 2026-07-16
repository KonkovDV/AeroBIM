"""Static honesty surface for product capabilities (not runtime probe results)."""

from __future__ import annotations

from dataclasses import asdict

from aerobim.domain.models import CapabilityState, CapabilityStatus, ReportCapabilities

_MEP_ALLOWED = frozenset(
    {
        CapabilityState.NOT_VERIFIED,
        CapabilityState.MISSING,
        CapabilityState.FAILED,
    }
)
_CALC_CORRECTNESS_ALLOWED = frozenset(
    {
        CapabilityState.NOT_IMPLEMENTED,
        CapabilityState.MISSING,
        CapabilityState.FAILED,
    }
)


def default_honesty_capabilities() -> ReportCapabilities:
    """Policy defaults: gaps stay MISSING / NOT_VERIFIED / NOT_IMPLEMENTED."""

    return ReportCapabilities()


def build_system_capabilities_payload() -> dict[str, object]:
    caps = default_honesty_capabilities()
    honesty = {
        "dwg_dxf": asdict(caps.dwg_dxf),
        "cv_human_level": asdict(caps.cv_human_level),
        "mep_system_clash": asdict(caps.mep_system_clash),
        "calculation_match": asdict(caps.calculation_match),
        "calculation_correctness": asdict(caps.calculation_correctness),
    }
    return {
        "artifact_type": "system_capabilities",
        "schema_version": "1.0.0",
        "claim_boundary": {
            "calculation_match": (
                "сверка результатов (numeric/provenance match) — PARTIAL when evaluated"
            ),
            "calculation_correctness": (
                "независимая проверка корректности расчёта — НЕ РЕАЛИЗОВАНО"
            ),
            "dwg_dxf": "НЕ РЕАЛИЗОВАНО",
            "cv_human_level": "НЕ РЕАЛИЗОВАНО",
            "mep_system_clash": "NOT VERIFIED",
        },
        "honesty": honesty,
        "forbidden_ok_states": {
            "dwg_dxf": [CapabilityState.OK.value],
            "cv_human_level": [CapabilityState.OK.value],
            "mep_system_clash": [CapabilityState.OK.value],
            "calculation_correctness": [CapabilityState.OK.value],
        },
        "notes": [
            (
                "Runtime report.capabilities may flip evaluated contours "
                "(clash/ids/raster) to ok/failed/skipped."
            ),
            (
                "Honesty fields above must not silently become ok without "
                "an explicit product delivery change."
            ),
        ],
    }


def assert_honesty_capabilities_not_silently_ok(capabilities: ReportCapabilities) -> None:
    """Architecture guard: declared gaps must not look delivered."""

    checks: tuple[tuple[str, CapabilityStatus, frozenset[CapabilityState]], ...] = (
        (
            "dwg_dxf",
            capabilities.dwg_dxf,
            frozenset({CapabilityState.MISSING, CapabilityState.FAILED}),
        ),
        (
            "cv_human_level",
            capabilities.cv_human_level,
            frozenset({CapabilityState.MISSING, CapabilityState.FAILED}),
        ),
        ("mep_system_clash", capabilities.mep_system_clash, _MEP_ALLOWED),
        (
            "calculation_correctness",
            capabilities.calculation_correctness,
            _CALC_CORRECTNESS_ALLOWED,
        ),
    )
    for name, status, allowed in checks:
        if status.status not in allowed:
            raise AssertionError(
                f"Honesty capability {name} has status {status.status.value!r}; "
                f"allowed={sorted(s.value for s in allowed)}"
            )


__all__ = [
    "assert_honesty_capabilities_not_silently_ok",
    "build_system_capabilities_payload",
    "default_honesty_capabilities",
]
