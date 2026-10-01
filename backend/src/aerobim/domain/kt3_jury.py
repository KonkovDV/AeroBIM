"""KT#3 jury gate: fail-closed fixture, GUID finding, tracker six tasks.

Does not close RT-001/002/003. Does not publish product accuracy.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any, Final

from aerobim.domain.checkpoint import CHECKPOINT

_RE_SHALL_BE = re.compile(r"shall be ([A-Za-z0-9]+)", re.I)
_RE_PROPERTY_VALUE = re.compile(r'property value "([^"]+)"', re.I)

CLAIM_LEVEL: Final = "fixture_and_proxy_only"
CLAIM_BOUNDARY: Final = (
    "KT#3 jury gate over the git fixture. Not product accuracy. "
    "Not customer SLA. Not MEP delivered. Checkpoint GO "
    "(regulatory_measurement_mvp; customer_go false). "
    "closes_rt001/002/003=false."
)
JURY_COMMAND: Final = "python -m aerobim.tools.run_kt3_jury"


class Kt3JuryError(ValueError):
    """Jury gate is not an honest KT#3 fixture show."""


def _expected_observed(raw: Mapping[str, Any]) -> tuple[Any, Any]:
    expected = raw.get("expected") or raw.get("expected_value")
    observed = raw.get("observed") or raw.get("observed_value")
    remark = str(raw.get("remark") or "")
    if expected in (None, "") and remark:
        match = _RE_SHALL_BE.search(remark)
        if match:
            expected = match.group(1)
    if observed in (None, "") and remark:
        match = _RE_PROPERTY_VALUE.search(remark)
        if match:
            observed = match.group(1)
    return expected, observed


def select_jury_finding(findings: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """First IFC/IDS finding with a GUID. Skip area rows with a null GUID."""

    for raw in findings:
        guid = str(raw.get("ifc_guid") or raw.get("element_guid") or "").strip()
        rule = str(raw.get("rule_id") or "")
        if not guid:
            continue
        if rule.upper().startswith("REQ-AREA"):
            continue
        expected, observed = _expected_observed(raw)
        remark = str(raw.get("remark") or "").strip()
        return {
            "finding_id": raw.get("finding_id"),
            "rule_id": rule,
            "ifc_guid": guid,
            "expected": expected,
            "observed": observed,
            "remark": remark[:500] if remark else None,
        }
    raise Kt3JuryError("no IFC/IDS finding with a GUID — do not show REQ-AREA first")


def require_kt3_jury_gate(gate: Mapping[str, Any]) -> dict[str, Any]:
    """Fail-loud: fixture must stay red, NO_GO, with a GUID-backed finding."""

    if gate.get("passed") is True:
        raise Kt3JuryError("fixture gate must not pass Shared-gate")
    verdict = gate.get("checkpoint_verdict")
    if verdict not in (None, CHECKPOINT):
        raise Kt3JuryError(f"checkpoint_verdict={verdict!r}")
    findings = gate.get("findings")
    if not isinstance(findings, list) or not findings:
        raise Kt3JuryError("gate has no IFC/IDS findings")
    typed = [row for row in findings if isinstance(row, dict)]
    jury = select_jury_finding(typed)
    raw_caps = gate.get("capabilities")
    caps: dict[str, Any] = raw_caps if isinstance(raw_caps, dict) else {}
    mep = str(caps.get("mep_system_clash") or "NOT_VERIFIED")
    if mep.upper() in {"OK", "DELIVERED"}:
        raise Kt3JuryError("mep_system_clash must not read as delivered on the fixture")
    return {
        "artifact_type": "kt3_jury_gate",
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "passed": False,
        "jury_finding": jury,
        "mep_system_clash": mep,
        "finding_count": int(gate.get("finding_count") or len(typed)),
        "command": JURY_COMMAND,
    }


__all__ = [
    "CLAIM_BOUNDARY",
    "CHECKPOINT",
    "JURY_COMMAND",
    "Kt3JuryError",
    "require_kt3_jury_gate",
    "select_jury_finding",
]
