"""Run manifest and reproducibility hash for package analyze (pilot DoD).

Claim boundary: fixture hashes prove deterministic Shared-gate stability, not
customer accuracy, SLA, or CDE import.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from aerobim.domain.architecture import DEFAULT_PACKAGE_STAGE_BUDGET, Contour, StageBudget
from aerobim.domain.package_outcome import PackageOutcome


class _ReportLike(Protocol):
    summary: Any
    issues: Sequence[Any]
    capabilities: Any | None


_CAPABILITY_FIELDS = (
    "clash",
    "ids",
    "ifc_validation",
    "dwg_dxf",
    "calculation_match",
    "mep_system_clash",
    "unit_scale",
    "quantity_consistency",
    "load_evidence",
)


def _is_advisory_issue(issue: Any) -> bool:
    rule_id = str(getattr(issue, "rule_id", "") or "")
    source_id = str(getattr(issue, "source_id", "") or "")
    if source_id == "compliance-agent":
        return True
    return rule_id.startswith("AGENT-") or rule_id.startswith("AEROBIM-AGENT-")


def engine_signature(report: _ReportLike) -> tuple[tuple[str, str, str, str, str], ...]:
    """Deterministic findings only — excludes advisory agent noise."""

    rows: list[tuple[str, str, str, str, str]] = []
    for issue in report.issues:
        if _is_advisory_issue(issue):
            continue
        category = getattr(issue, "category", "")
        category_value = category.value if hasattr(category, "value") else str(category)
        severity = getattr(issue, "severity", "")
        severity_value = severity.value if hasattr(severity, "value") else str(severity)
        rows.append(
            (
                str(getattr(issue, "rule_id", "") or ""),
                severity_value,
                category_value,
                str(getattr(issue, "target_ref", "") or ""),
                str(getattr(issue, "message", "") or ""),
            )
        )
    return tuple(sorted(rows))


def capability_digest(report: _ReportLike) -> dict[str, str]:
    caps = report.capabilities
    if caps is None:
        return {}
    digest: dict[str, str] = {}
    for name in _CAPABILITY_FIELDS:
        field = getattr(caps, name, None)
        if field is None:
            continue
        status = getattr(field, "status", field)
        digest[name] = status.value if hasattr(status, "value") else str(status)
    return digest


def _canonical_json(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )


def compute_reproducibility_hash(
    *,
    passed: bool,
    outcome: PackageOutcome | str | None,
    engine: Sequence[tuple[str, str, str, str, str]],
    capabilities: Mapping[str, str],
    package_sha256: str | None = None,
    rules_sha256: str | None = None,
    config_sha256: str | None = None,
    code_version: str | None = None,
) -> str:
    """Stable digest over deterministic report inputs (excludes report_id / timestamps)."""

    outcome_value = outcome.value if isinstance(outcome, PackageOutcome) else str(outcome or "")
    payload: dict[str, Any] = {
        "passed": bool(passed),
        "outcome": outcome_value,
        "engine": list(engine),
        "capabilities": dict(sorted(capabilities.items())),
    }
    inputs: dict[str, str] = {}
    if package_sha256:
        inputs["package_sha256"] = package_sha256
    if rules_sha256:
        inputs["rules_sha256"] = rules_sha256
    if config_sha256:
        inputs["config_sha256"] = config_sha256
    if code_version:
        inputs["code_version"] = code_version
    if inputs:
        payload["inputs"] = inputs
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def compute_report_reproducibility_hash(
    report: _ReportLike,
    *,
    package_sha256: str | None = None,
    rules_sha256: str | None = None,
    config_sha256: str | None = None,
    code_version: str | None = None,
) -> str:
    summary = report.summary
    outcome = getattr(summary, "outcome", None)
    return compute_reproducibility_hash(
        passed=bool(getattr(summary, "passed", False)),
        outcome=outcome,
        engine=engine_signature(report),
        capabilities=capability_digest(report),
        package_sha256=package_sha256,
        rules_sha256=rules_sha256,
        config_sha256=config_sha256,
        code_version=code_version,
    )


@dataclass(frozen=True)
class RunManifest:
    """Immutable analyze-run manifest for evidence bundles and pilot audit."""

    schema_version: str
    request_id: str
    pack_id: str | None
    reproducibility_hash: str
    passed: bool
    outcome: str
    engine_finding_count: int
    capability_digest: dict[str, str]
    stage_budget: dict[str, float]
    contours: tuple[str, ...]
    package_sha256: str | None = None
    rules_sha256: str | None = None
    config_sha256: str | None = None
    code_version: str | None = None
    claim_boundary: str = "fixture-only; not customer accuracy"

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "pack_id": self.pack_id,
            "reproducibility_hash": self.reproducibility_hash,
            "passed": self.passed,
            "outcome": self.outcome,
            "engine_finding_count": self.engine_finding_count,
            "capability_digest": self.capability_digest,
            "stage_budget": self.stage_budget,
            "contours": list(self.contours),
            "package_sha256": self.package_sha256,
            "rules_sha256": self.rules_sha256,
            "config_sha256": self.config_sha256,
            "code_version": self.code_version,
            "claim_boundary": self.claim_boundary,
        }


def build_run_manifest(
    report: _ReportLike,
    *,
    request_id: str,
    pack_id: str | None = None,
    package_sha256: str | None = None,
    rules_sha256: str | None = None,
    config_sha256: str | None = None,
    code_version: str | None = None,
    stage_budget: StageBudget | None = None,
) -> RunManifest:
    budget = stage_budget or DEFAULT_PACKAGE_STAGE_BUDGET
    summary = report.summary
    outcome = getattr(summary, "outcome", None)
    if isinstance(outcome, PackageOutcome):
        outcome_value = outcome.value
    elif outcome is not None and hasattr(outcome, "value"):
        outcome_value = str(outcome.value)
    else:
        outcome_value = str(outcome or "")
    engine = engine_signature(report)
    caps = capability_digest(report)
    return RunManifest(
        schema_version="1.0.0",
        request_id=request_id,
        pack_id=pack_id,
        reproducibility_hash=compute_report_reproducibility_hash(
            report,
            package_sha256=package_sha256,
            rules_sha256=rules_sha256,
            config_sha256=config_sha256,
            code_version=code_version,
        ),
        passed=bool(getattr(summary, "passed", False)),
        outcome=outcome_value,
        engine_finding_count=len(engine),
        capability_digest=caps,
        stage_budget=budget.as_dict(),
        contours=tuple(contour.value for contour in Contour),
        package_sha256=package_sha256,
        rules_sha256=rules_sha256,
        config_sha256=config_sha256,
        code_version=code_version,
    )


__all__ = [
    "RunManifest",
    "build_run_manifest",
    "capability_digest",
    "compute_report_reproducibility_hash",
    "compute_reproducibility_hash",
    "engine_signature",
]
