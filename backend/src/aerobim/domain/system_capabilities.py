"""Static honesty surface for product capabilities (not runtime probe results)."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from aerobim.domain.models import CapabilityState, CapabilityStatus, ReportCapabilities

_MEP_ALLOWED = frozenset(
    {
        CapabilityState.NOT_VERIFIED,
        CapabilityState.MISSING,
        CapabilityState.FAILED,
    }
)
_DWG_DXF_ALLOWED = frozenset(
    {
        CapabilityState.MISSING,
        CapabilityState.FAILED,
        CapabilityState.NOT_VERIFIED,
        CapabilityState.SKIPPED,
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


def load_customer_intake_gate_snapshot() -> dict[str, Any]:
    """Best-effort load of audit/evidence/customer-intake-gate.json for honesty API."""

    candidates = [
        Path(__file__).resolve().parents[4] / "audit" / "evidence" / "customer-intake-gate.json",
        Path.cwd() / "audit" / "evidence" / "customer-intake-gate.json",
    ]
    for path in candidates:
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        gates = payload.get("gates") if isinstance(payload, dict) else None
        true_gates = (
            [key for key, value in gates.items() if value is True]
            if isinstance(gates, dict)
            else []
        )
        return {
            "status": payload.get("status", "UNKNOWN"),
            "claim_level": payload.get("claim_level", "unknown"),
            "true_gates": true_gates,
            "checkpoint": "NO_GO",
            "source": str(path.as_posix()),
        }
    return {
        "status": "MISSING_GATE_FILE",
        "claim_level": "not_ready",
        "true_gates": [],
        "checkpoint": "NO_GO",
        "source": None,
    }


def build_system_capabilities_payload() -> dict[str, object]:
    caps = default_honesty_capabilities()
    honesty = {
        "dwg_dxf": asdict(caps.dwg_dxf),
        "cv_human_level": asdict(caps.cv_human_level),
        "mep_system_clash": asdict(caps.mep_system_clash),
        "calculation_match": asdict(caps.calculation_match),
        "calculation_correctness": asdict(caps.calculation_correctness),
    }
    intake = load_customer_intake_gate_snapshot()
    return {
        "artifact_type": "system_capabilities",
        "schema_version": "1.1.0",
        "claim_boundary": {
            "calculation_match": (
                "сверка результатов (numeric/provenance match) — PARTIAL when evaluated"
            ),
            "calculation_correctness": (
                "независимая проверка корректности расчёта — НЕ РЕАЛИЗОВАНО"
            ),
            "dwg_dxf": ("DXF partial via optional ezdxf; native DWG / ODA NOT VERIFIED — never OK"),
            "cv_human_level": "НЕ РЕАЛИЗОВАНО",
            "mep_system_clash": ("DI-wired Unconfigured provider (MEP-CLASH-001) — NOT VERIFIED"),
            "precision_claim": (
                "Publishable only with customer corpus + ≥2 adjudicators + κ/α agreement"
            ),
            "customer_sla": "Fixture SLA ≠ customer комплект SLA",
        },
        "honesty": honesty,
        "customer_intake_gate": intake,
        "forbidden_ok_states": {
            "dwg_dxf": [CapabilityState.OK.value],
            "cv_human_level": [CapabilityState.OK.value],
            "mep_system_clash": [CapabilityState.OK.value],
            "calculation_correctness": [CapabilityState.OK.value],
        },
        "notes": [
            (
                "Runtime report.capabilities may flip evaluated contours "
                "(clash/ids/raster/dxf) to ok/failed/skipped/not_verified."
            ),
            (
                "Honesty fields above must not silently become ok without "
                "an explicit product delivery change."
            ),
            "Checkpoint remains NO_GO until RT-001/002/003 customer evidence.",
        ],
    }


def assert_honesty_capabilities_not_silently_ok(capabilities: ReportCapabilities) -> None:
    """Architecture guard: declared gaps must not look delivered."""

    checks: tuple[tuple[str, CapabilityStatus, frozenset[CapabilityState]], ...] = (
        ("dwg_dxf", capabilities.dwg_dxf, _DWG_DXF_ALLOWED),
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
    "load_customer_intake_gate_snapshot",
]
