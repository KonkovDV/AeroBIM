"""WP-02: HybridRouteGate mandatory pre-gate on advisory contour."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock

from aerobim.application.services.hybrid_route_gate import HybridRouteGate
from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.hybrid import RouteTarget
from aerobim.domain.models import (
    FindingCategory,
    GeneratedRemark,
    RequirementSource,
    Severity,
    ValidationIssue,
    ValidationRequest,
)


class _Empty:
    def extract(self, _source):
        return []

    def synthesize(self, _source):
        return []

    def analyze(self, _source):
        return []


class _Remark:
    def generate(self, issue):
        return GeneratedRemark(title=issue.rule_id, body=issue.message)


class _Store:
    def __init__(self) -> None:
        self.report = None

    def save(self, report):
        self.report = report
        return report.report_id

    def get(self, report_id):
        if self.report is not None and self.report.report_id == report_id:
            return self.report
        return None


def _build(
    *,
    advisory_issues: tuple[ValidationIssue, ...] = (),
    hybrid_route_gate: HybridRouteGate | None = None,
) -> AnalyzeProjectPackageUseCase:
    empty = _Empty()
    return AnalyzeProjectPackageUseCase(
        requirement_extractor=empty,
        narrative_rule_synthesizer=empty,
        drawing_analyzer=empty,
        ifc_validator=MagicMock(validate=MagicMock(return_value=[])),
        ids_validator=MagicMock(validate=MagicMock(return_value=[])),
        remark_generator=_Remark(),
        audit_report_store=_Store(),
        advisory_issues=advisory_issues,
        hybrid_route_gate=hybrid_route_gate,
        signoff_profile="fixture",
    )


def _request(*, tenant_id: str | None, ifc_name: str = "samples/ifc/wall.ifc") -> ValidationRequest:
    return ValidationRequest(
        request_id="wp02-req",
        ifc_path=Path(ifc_name),
        requirement_source=RequirementSource(),
        ids_path=Path("dummy.ids"),
        tenant_id=tenant_id,
        project_id="proj-wp02",
    )


def _fake_advisory(rule_id: str = "ADVISORY-FAKE") -> tuple[ValidationIssue, ...]:
    return (
        ValidationIssue(
            rule_id=rule_id,
            severity=Severity.ERROR,
            message="advisory observation",
            category=FindingCategory.IFC_VALIDATION,
            origin="advisory",
        ),
    )


class Wp02HybridAdvisoryPreGateTests(unittest.TestCase):
    def test_missing_gate_suppresses_advisory(self) -> None:
        report = _build(advisory_issues=_fake_advisory(), hybrid_route_gate=None).execute(
            _request(tenant_id="tenant-a")
        )
        self.assertFalse(any(i.rule_id == "ADVISORY-FAKE" for i in report.issues))
        gate_rows = [t for t in report.tool_traces if t.get("tool") == "hybrid_route_gate"]
        self.assertEqual(len(gate_rows), 1)
        self.assertEqual(gate_rows[0].get("status"), "blocked")
        self.assertEqual(gate_rows[0].get("egress_bytes_estimate"), 0)

    def test_empty_tenant_blocks_advisory_observations(self) -> None:
        report = _build(
            advisory_issues=_fake_advisory(), hybrid_route_gate=HybridRouteGate()
        ).execute(_request(tenant_id=""))
        self.assertFalse(any(i.rule_id == "ADVISORY-FAKE" for i in report.issues))
        gate_rows = [t for t in report.tool_traces if t.get("tool") == "hybrid_route_gate"]
        self.assertEqual(gate_rows[0].get("allowed"), False)
        self.assertEqual(gate_rows[0].get("may_call_external"), False)

    def test_local_route_with_tenant_records_gate_allow(self) -> None:
        report = _build(
            advisory_issues=_fake_advisory("ADVISORY-OK"),
            hybrid_route_gate=HybridRouteGate(),
        ).execute(_request(tenant_id="tenant-a"))
        gate_rows = [t for t in report.tool_traces if t.get("tool") == "hybrid_route_gate"]
        self.assertEqual(gate_rows[0].get("allowed"), True)
        self.assertEqual(gate_rows[0].get("status"), "local")
        self.assertEqual(gate_rows[0].get("egress_bytes_estimate"), 0)
        self.assertEqual(gate_rows[0].get("verdict_impact"), "none")

    def test_gate_block_does_not_flip_summary_passed(self) -> None:
        off = _build(hybrid_route_gate=HybridRouteGate()).execute(_request(tenant_id="tenant-a"))
        blocked = _build(
            advisory_issues=_fake_advisory(), hybrid_route_gate=HybridRouteGate()
        ).execute(_request(tenant_id=""))
        self.assertEqual(off.summary.passed, blocked.summary.passed)

    def test_cannot_egress_without_mask_even_if_public_target(self) -> None:
        result = HybridRouteGate().evaluate(
            object_kind="public_fixture",
            target=RouteTarget.PUBLIC,
            tenant_id="tenant-a",
            task_type="test",
            request_id="r1",
            payload={"secret_field": "nope"},
            mask_rules=None,
        )
        self.assertFalse(result.may_call_external)
        self.assertEqual(result.egress_bytes_estimate, 0)


if __name__ == "__main__":
    unittest.main()
