"""IFC Acceptance Gate projector — fixture contract, ADR-001, no customer accuracy."""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.ifc_acceptance_gate import (
    AcceptanceGateError,
    project_ifc_acceptance_gate,
    require_fixture_gate,
)
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    FindingCategory,
    ReportCapabilities,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.domain.package_outcome import PackageOutcome


def _issue(**kwargs: object) -> ValidationIssue:
    payload = {
        "rule_id": "IDS-WALL-001",
        "severity": Severity.ERROR,
        "message": "missing FireRating",
        "category": FindingCategory.IDS_VALIDATION,
        "element_guid": "GUID-1",
        "finding_id": "F-0001",
        "source_id": "model.ifc",
        "evidence_refs": ("ifc://GUID-1",),
        "expected_value": "Pset_WallCommon.FireRating=REI60",
        "observed_value": None,
    }
    payload.update(kwargs)
    return ValidationIssue(**payload)  # type: ignore[arg-type]


def _report(
    *, passed: bool, outcome: PackageOutcome, issues: tuple[ValidationIssue, ...]
) -> ValidationReport:
    return ValidationReport(
        report_id="r1",
        request_id="q1",
        ifc_path=Path("m.ifc"),
        created_at="2026-08-16T00:00:00Z",
        requirements=(),
        issues=issues,
        summary=ValidationSummary(1, len(issues), 1, 0, passed, outcome=outcome),
        capabilities=ReportCapabilities(
            ids=CapabilityStatus(CapabilityState.FAILED, "ids facet failed"),
            ifc_validation=CapabilityStatus(CapabilityState.OK, "properties ran"),
            ifc_schema=CapabilityStatus(CapabilityState.OK, "schema ok"),
            clash=CapabilityStatus(CapabilityState.NOT_VERIFIED, "not in gate"),
        ),
    )


class IfcAcceptanceGateTests(unittest.TestCase):
    def test_projects_ids_finding_and_capability_honesty(self) -> None:
        gate = project_ifc_acceptance_gate(
            _report(
                passed=False,
                outcome=PackageOutcome.FAILED,
                issues=(_issue(),),
            ),
            engine_version="abc",
            rule_pack_hash="ids-hash",
            input_hash="in-hash",
            created_at="2026-08-16T00:00:00Z",
            reproducibility_hash="rep",
        )
        self.assertEqual(gate["outcome"], "failed")
        self.assertFalse(gate["passed"])
        self.assertEqual(gate["checkpoint_verdict"], CHECKPOINT)
        self.assertEqual(gate["capabilities"]["ids_validation"], "FAILED")
        self.assertEqual(gate["capabilities"]["geometry"], "NOT_VERIFIED")
        self.assertEqual(gate["findings"][0]["ifc_guid"], "GUID-1")
        self.assertEqual(gate["findings"][0]["rule_id"], "IDS-WALL-001")
        require_fixture_gate(gate)

    def test_rejects_adr001_mismatch(self) -> None:
        with self.assertRaises(AcceptanceGateError):
            project_ifc_acceptance_gate(
                _report(
                    passed=False,
                    outcome=PackageOutcome.PASS_WITH_WARNINGS,
                    issues=(_issue(),),
                ),
                engine_version=None,
                rule_pack_hash=None,
                input_hash=None,
                created_at=None,
            )

    def test_drops_advisory_and_drawing_findings(self) -> None:
        drawing = _issue(
            rule_id="DRAW-1",
            category=FindingCategory.DRAWING_VALIDATION,
            finding_id="F-d",
        )
        advisory = _issue(
            rule_id="AGENT-1",
            origin="advisory",
            finding_id="F-a",
        )
        gate = project_ifc_acceptance_gate(
            _report(
                passed=False,
                outcome=PackageOutcome.FAILED,
                issues=(drawing, advisory, _issue()),
            ),
            engine_version=None,
            rule_pack_hash=None,
            input_hash=None,
            created_at=None,
        )
        self.assertEqual(len(gate["findings"]), 1)
        self.assertEqual(gate["findings"][0]["finding_id"], "F-0001")
        self.assertEqual(gate["outcome_scope"], "full_package")
        self.assertEqual(gate["findings_scope"], "ifc_ids")
        self.assertEqual(gate["blocking_outside_projection_count"], 1)
        self.assertEqual(gate["outside_projection_blocking"][0]["rule_id"], "DRAW-1")
        self.assertEqual(gate["schema_version"], "1.1.0")

    def test_package_completeness_error_is_visible_outside_ifc_ids_projection(self) -> None:
        completeness = _issue(
            rule_id="AEROBIM-PACKAGE-INVENTORY-MISSING",
            category=FindingCategory.CROSS_DOCUMENT,
            finding_id="F-pc",
            source_id="package-completeness",
        )
        gate = project_ifc_acceptance_gate(
            _report(passed=False, outcome=PackageOutcome.FAILED, issues=(completeness,)),
            engine_version=None,
            rule_pack_hash=None,
            input_hash=None,
            created_at=None,
        )
        self.assertFalse(gate["passed"])
        self.assertEqual(gate["outcome"], "failed")
        self.assertEqual(gate["finding_count"], 0)
        self.assertEqual(gate["blocking_finding_count"], 0)
        self.assertEqual(gate["blocking_outside_projection_count"], 1)
        self.assertEqual(
            gate["outside_projection_blocking"][0]["source_id"], "package-completeness"
        )
        with self.assertRaises(AcceptanceGateError):
            require_fixture_gate(gate)

    def test_warning_outside_projection_is_not_blocking(self) -> None:
        drawing = _issue(
            rule_id="DRAW-W",
            category=FindingCategory.DRAWING_VALIDATION,
            severity=Severity.WARNING,
            finding_id="F-w",
        )
        gate = project_ifc_acceptance_gate(
            _report(passed=False, outcome=PackageOutcome.FAILED, issues=(drawing,)),
            engine_version=None,
            rule_pack_hash=None,
            input_hash=None,
            created_at=None,
        )
        self.assertEqual(gate["blocking_outside_projection_count"], 0)
        self.assertEqual(gate["outside_projection_blocking"], [])

    def test_require_fixture_gate_rejects_green_or_empty(self) -> None:
        green = project_ifc_acceptance_gate(
            _report(passed=True, outcome=PackageOutcome.PASS, issues=(_issue(),)),
            engine_version=None,
            rule_pack_hash=None,
            input_hash=None,
            created_at=None,
        )
        with self.assertRaises(AcceptanceGateError):
            require_fixture_gate(green)
        empty = project_ifc_acceptance_gate(
            _report(passed=False, outcome=PackageOutcome.FAILED, issues=()),
            engine_version=None,
            rule_pack_hash=None,
            input_hash=None,
            created_at=None,
        )
        with self.assertRaises(AcceptanceGateError):
            require_fixture_gate(empty)


if __name__ == "__main__":
    unittest.main()
