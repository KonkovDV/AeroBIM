"""coverage_from_report: bridge a real ValidationReport to a check-coverage map.

Honest bridge: source_ids come from DECLARED inputs; engine-internal finding sources
surface as (unattributed); scope=None never fabricates CHECKED_OK; explicit scope
enables it. Verdict-neutral.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.check_coverage import CoverageStatus, coverage_from_report
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    FindingCategory,
    ParsedRequirement,
    ReportCapabilities,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)

_IFC = FindingCategory.IFC_VALIDATION
_IDS = FindingCategory.IDS_VALIDATION


def _issue(
    source_id: str | None, category: FindingCategory, *, origin: str = "deterministic"
) -> ValidationIssue:
    return ValidationIssue(
        rule_id="r",
        severity=Severity.ERROR,
        message="m",
        category=category,
        source_id=source_id,
        origin=origin,  # type: ignore[arg-type]
    )


def _report(
    *,
    requirements: tuple[ParsedRequirement, ...] = (),
    issues: tuple[ValidationIssue, ...] = (),
    capabilities: ReportCapabilities | None = None,
) -> ValidationReport:
    return ValidationReport(
        report_id="rep",
        request_id="req",
        ifc_path=Path("m.ifc"),
        created_at="2026-07-29T00:00:00Z",
        requirements=requirements,
        issues=issues,
        summary=ValidationSummary(
            requirement_count=len(requirements),
            issue_count=len(issues),
            error_count=0,
            warning_count=0,
            passed=True,
        ),
        capabilities=capabilities,
    )


class CoverageFromReportTests(unittest.TestCase):
    def test_declared_source_with_finding_is_checked_findings(self) -> None:
        report = _report(
            requirements=(ParsedRequirement(rule_id="r", source="req-doc"),),
            issues=(_issue("req-doc", _IFC),),
        )
        row = next(r for r in coverage_from_report(report).rows if r.source_id == "req-doc")
        self.assertEqual(row.status_for(_IFC), CoverageStatus.CHECKED_FINDINGS)

    def test_scope_none_never_fabricates_checked_ok(self) -> None:
        report = _report(
            requirements=(ParsedRequirement(rule_id="r", source="req-doc"),),
            capabilities=ReportCapabilities(ids=CapabilityStatus(CapabilityState.OK)),
        )
        row = next(r for r in coverage_from_report(report).rows if r.source_id == "req-doc")
        for _family, status in row.families:
            self.assertNotEqual(status, CoverageStatus.CHECKED_OK)

    def test_engine_finding_surfaces_as_unattributed(self) -> None:
        report = _report(
            requirements=(ParsedRequirement(rule_id="r", source="req-doc"),),
            issues=(_issue("clash", FindingCategory.SPATIAL),),
        )
        row = next(r for r in coverage_from_report(report).rows if r.source_id == "(unattributed)")
        self.assertEqual(row.status_for(FindingCategory.SPATIAL), CoverageStatus.CHECKED_FINDINGS)

    def test_verdict_neutral(self) -> None:
        report = _report(requirements=(ParsedRequirement(rule_id="r", source="req-doc"),))
        self.assertNotIn('"passed"', json.dumps(coverage_from_report(report).to_dict()))

    def test_explicit_scope_enables_checked_ok(self) -> None:
        report = _report(
            requirements=(ParsedRequirement(rule_id="r", source="req-doc"),),
            capabilities=ReportCapabilities(ids=CapabilityStatus(CapabilityState.OK)),
        )
        cov = coverage_from_report(report, scope={_IDS: {"req-doc"}})
        row = next(r for r in cov.rows if r.source_id == "req-doc")
        self.assertEqual(row.status_for(_IDS), CoverageStatus.CHECKED_OK)


if __name__ == "__main__":
    unittest.main()
