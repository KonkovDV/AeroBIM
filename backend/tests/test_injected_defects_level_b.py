"""P-012 Level B: injected defects with deterministic expected outcomes.

Catalog: samples/benchmarks/injected-defects-level-b.json.
- detected: the defect MUST produce its expected finding (engine regression);
- control_clean: SI-equivalent values must NOT be false-flagged;
- known_undetected: VERIFIED detection boundary (free-text numbers are not
  сверка) -- if the engine ever starts detecting it, this test fails so the
  catalog and Claims wording get updated consciously.
"""

from __future__ import annotations

import json
from pathlib import Path

from aerobim.domain.models import RequirementSource, Severity, SourceKind, ValidationRequest
from aerobim.infrastructure.adapters.spreadsheet_load_evidence_adapter import (
    SpreadsheetLoadEvidenceAdapter,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CATALOG = _REPO_ROOT / "samples" / "benchmarks" / "injected-defects-level-b.json"


def _defects() -> list[dict[str, object]]:
    data = json.loads(_CATALOG.read_text(encoding="utf-8"))
    defects = data["defects"]
    assert isinstance(defects, list) and defects
    return [d for d in defects if isinstance(d, dict)]


def _verify(calculation_text: str):
    request = ValidationRequest(
        request_id="level-b-defect",
        ifc_path=_REPO_ROOT / "samples" / "ifc" / "walls-multi-entity.ifc",
        requirement_source=RequirementSource(
            text="", source_kind=SourceKind.STRUCTURED_TEXT, source_id="level-b-req"
        ),
        calculation_source=RequirementSource(
            text=calculation_text,
            source_kind=SourceKind.CALCULATION,
            source_id="level-b-defect",
        ),
    )
    return SpreadsheetLoadEvidenceAdapter().verify(request)


def test_detected_defects_yield_expected_findings() -> None:
    failures: list[str] = []
    for defect in _defects():
        if defect.get("expected_status") != "detected":
            continue
        issues = _verify(str(defect["calculation_text"]))
        rule_ids = {issue.rule_id for issue in issues}
        if str(defect["expected_finding"]) not in rule_ids:
            failures.append(f"{defect['defect_id']}: got {sorted(rule_ids)}")
    assert not failures, "Injected defects NOT detected:\n" + "\n".join(failures)


def test_detected_defects_carry_expected_severity() -> None:
    for defect in _defects():
        if defect.get("expected_status") != "detected":
            continue
        issues = _verify(str(defect["calculation_text"]))
        matched = [i for i in issues if i.rule_id == str(defect["expected_finding"])]
        assert matched, defect["defect_id"]
        assert matched[0].severity is Severity(str(defect["expected_severity"]))


def test_si_equivalent_values_are_not_false_flagged() -> None:
    for defect in _defects():
        if defect.get("expected_status") != "control_clean":
            continue
        issues = _verify(str(defect["calculation_text"]))
        mismatches = [i for i in issues if i.rule_id == "AEROBIM-LOAD-MISMATCH"]
        assert not mismatches, f"{defect['defect_id']}: false mismatch {mismatches}"


def test_known_undetected_boundary_stays_documented() -> None:
    # Honesty anchor: free-text numeric mutation currently yields only the
    # LOAD-FORMAT info (no numeric comparison happened). If detection appears,
    # update the catalog + Claims wording -- consciously, not silently.
    for defect in _defects():
        if defect.get("expected_status") != "known_undetected":
            continue
        issues = _verify(str(defect["calculation_text"]))
        rule_ids = sorted({issue.rule_id for issue in issues})
        assert rule_ids == [str(defect["expected_finding"])], (
            f"{defect['defect_id']}: boundary shifted, got {rule_ids}; "
            "update injected-defects catalog and Claims wording"
        )
