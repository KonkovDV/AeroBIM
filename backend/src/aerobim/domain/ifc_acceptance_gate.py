
"""IFC Acceptance Gate projection — product-path report contract.

Claim boundary: fixture/engineering contract only. Not customer accuracy,
not TZ >90%, not CDE-ready, not native DWG. ``passed`` follows ADR-001:
true only for ``pass`` / ``pass_with_warnings``. Never emit
``PASS_WITH_WARNINGS`` with ``passed=false``.

``outcome`` / ``passed`` follow the full package (``outcome_scope=full_package``).
``findings`` stay IFC/IDS (``findings_scope=ifc_ids``). Errors outside that
projection are counted in ``blocking_outside_projection_count`` so a red
package cannot look empty on the product face.
"""

from __future__ import annotations

from typing import Any

from aerobim.domain.advisory_origin import is_advisory_issue
from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.models import FindingCategory, Severity
from aerobim.domain.package_outcome import PackageOutcome, summary_passed_from_outcome

SCHEMA_VERSION = "1.1.0"
ARTIFACT_TYPE = "aerobim_ifc_acceptance_gate"
CLAIM_BOUNDARY = (
    "IFC Acceptance Gate fixture contract. Checkpoint GO "
    "(regulatory_measurement_mvp; customer_go false). "
    "Not product accuracy. Not TZ >90%. Not CDE-ready. Not native DWG. "
    "Not MEP delivered. Overlay/CV never writes summary.passed."
)

_ACCEPTANCE_CATEGORIES = frozenset(
    {
        FindingCategory.IDS_VALIDATION.value,
        FindingCategory.IFC_VALIDATION.value,
        "ids-validation",
        "ifc-validation",
    }
)


class AcceptanceGateError(RuntimeError):
    """Operator-visible failure: gate contract not met."""


def _field(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _enum_value(raw: Any) -> str | None:
    if raw is None:
        return None
    if hasattr(raw, "value"):
        return str(raw.value)
    return str(raw)


def _capability_state(caps: Any, name: str) -> str:
    if caps is None:
        return "NOT_VERIFIED"
    status = _field(caps, name)
    if status is None:
        return "NOT_VERIFIED"
    if isinstance(status, dict):
        state = status.get("status")
    else:
        state = _field(status, "status")
    value = _enum_value(state)
    if not value:
        return "NOT_VERIFIED"
    return value.upper()


def _remark_text(issue: Any) -> str | None:
    remark = _field(issue, "remark")
    if remark is None:
        return None
    if isinstance(remark, dict):
        body = remark.get("body")
        return str(body) if body else None
    body = getattr(remark, "body", None)
    return str(body) if body else None


def _is_blocking_severity(severity: str | None) -> bool:
    return (severity or "").lower() == Severity.ERROR.value


def _in_acceptance_projection(issue: Any) -> bool:
    category = _enum_value(_field(issue, "category")) or ""
    return category in _ACCEPTANCE_CATEGORIES


def _acceptance_finding(issue: Any) -> dict[str, Any] | None:
    if is_advisory_issue(issue):
        return None
    if not _in_acceptance_projection(issue):
        return None
    category = _enum_value(_field(issue, "category")) or ""
    evidence = _field(issue, "evidence_refs") or ()
    evidence_refs: tuple[str, ...]
    if isinstance(evidence, str):
        evidence_refs = (evidence,)
    else:
        evidence_refs = tuple(str(item) for item in evidence)
    return {
        "finding_id": _field(issue, "finding_id"),
        "rule_id": _field(issue, "rule_id"),
        "severity": _enum_value(_field(issue, "severity")),
        "category": category,
        "ifc_guid": _field(issue, "element_guid"),
        "source_id": _field(issue, "source_id"),
        "evidence_refs": list(evidence_refs),
        "expected": _field(issue, "expected_value"),
        "observed": _field(issue, "observed_value"),
        "remark": _remark_text(issue) or _field(issue, "message"),
    }


def project_ifc_acceptance_gate(
    report: Any,
    *,
    engine_version: str | None,
    rule_pack_hash: str | None,
    input_hash: str | None,
    created_at: str | None,
    reproducibility_hash: str | None = None,
) -> dict[str, Any]:
    """Project the product-path Acceptance Gate contract from a package report."""

    summary = _field(report, "summary")
    if summary is None:
        raise AcceptanceGateError("report has no summary")
    outcome_raw = _field(summary, "outcome")
    passed = bool(_field(summary, "passed"))
    if outcome_raw is not None:
        try:
            outcome = (
                outcome_raw
                if isinstance(outcome_raw, PackageOutcome)
                else PackageOutcome(str(_enum_value(outcome_raw)))
            )
        except ValueError as exc:
            raise AcceptanceGateError(f"unknown package outcome: {outcome_raw!r}") from exc
        derived = summary_passed_from_outcome(outcome)
        if derived != passed:
            raise AcceptanceGateError(
                "ADR-001 violation: summary.passed must follow PackageOutcome "
                f"(outcome={outcome.value}, passed={passed})"
            )
        outcome_value = outcome.value
    else:
        outcome_value = "pass" if passed else "failed"

    caps = _field(report, "capabilities")
    issues = tuple(_field(report, "issues") or ())
    findings = [row for issue in issues if (row := _acceptance_finding(issue)) is not None]
    blocking = [row for row in findings if _is_blocking_severity(row.get("severity"))]
    outside_projection_blocking = [
        {
            "finding_id": _field(issue, "finding_id"),
            "rule_id": _field(issue, "rule_id"),
            "severity": _enum_value(_field(issue, "severity")),
            "category": _enum_value(_field(issue, "category")),
            "source_id": _field(issue, "source_id"),
        }
        for issue in issues
        if not is_advisory_issue(issue)
        and not _in_acceptance_projection(issue)
        and _is_blocking_severity(_enum_value(_field(issue, "severity")))
    ]
    return {
        "artifact_type": ARTIFACT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "claim_boundary": CLAIM_BOUNDARY,
        "checkpoint_verdict": CHECKPOINT,
        "customer_accuracy": False,
        "outcome_scope": "full_package",
        "findings_scope": "ifc_ids",
        "outcome": outcome_value,
        "passed": passed,
        "finding_count": len(findings),
        "blocking_finding_count": len(blocking),
        "blocking_outside_projection_count": len(outside_projection_blocking),
        "outside_projection_blocking": outside_projection_blocking,
        "capabilities": {
            "ifc_schema": _capability_state(caps, "ifc_schema"),
            "ids_validation": _capability_state(caps, "ids"),
            "property_validation": _capability_state(caps, "ifc_validation"),
            "geometry": _capability_state(caps, "clash"),
            "dwg_native": _capability_state(caps, "dwg_dxf"),
            "mep_system_clash": _capability_state(caps, "mep_system_clash"),
        },
        "findings": findings,
        "manifest": {
            "engine_version": engine_version,
            "rule_pack_hash": rule_pack_hash,
            "input_hash": input_hash,
            "reproducibility_hash": reproducibility_hash,
            "created_at": created_at,
        },
    }


def require_fixture_gate(gate: dict[str, Any]) -> None:
    """Fail-loud for the demo fixture: blocked package with IFC/IDS evidence."""

    if gate.get("passed") is True:
        raise AcceptanceGateError(
            "fixture Acceptance Gate must not pass Shared-gate; this demo is fail-closed"
        )
    if not gate.get("findings"):
        raise AcceptanceGateError(
            "no IFC/IDS findings — not an Acceptance Gate demo (drawing-only is P1)"
        )
