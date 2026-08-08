"""coverage_from_report: bridge a real ValidationReport to a check-coverage map.

Honest bridge: source_ids come from DECLARED inputs; engine-internal finding sources
surface as (unattributed); scope=None never fabricates CHECKED_OK; explicit scope
enables it. Verdict-neutral.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.check_coverage import CoverageStatus, coverage_from_report, derive_report_scope
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    DrawingAsset,
    DrawingRegionRef,
    FindingCategory,
    ParsedRequirement,
    ReportCapabilities,
    RuleScope,
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
    drawing_assets: tuple[DrawingAsset, ...] = (),
    drawing_regions: tuple[DrawingRegionRef, ...] = (),
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
        drawing_assets=drawing_assets,
        drawing_regions=drawing_regions,
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

    def test_coverage_invariant_under_verdict_flip(self) -> None:
        # Flipping summary.passed must not change the coverage map (verdict-neutral).
        reqs = (ParsedRequirement(rule_id="r", source="req-doc"),)
        issues = (_issue("req-doc", _IFC),)
        passed = _report(requirements=reqs, issues=issues)
        failed = ValidationReport(
            report_id=passed.report_id,
            request_id=passed.request_id,
            ifc_path=passed.ifc_path,
            created_at=passed.created_at,
            requirements=reqs,
            issues=issues,
            summary=ValidationSummary(
                requirement_count=1, issue_count=1, error_count=1, warning_count=0, passed=False
            ),
            capabilities=passed.capabilities,
        )
        self.assertEqual(
            coverage_from_report(passed).to_dict(), coverage_from_report(failed).to_dict()
        )

    def test_explicit_scope_enables_checked_ok(self) -> None:
        report = _report(
            requirements=(ParsedRequirement(rule_id="r", source="req-doc"),),
            capabilities=ReportCapabilities(ids=CapabilityStatus(CapabilityState.OK)),
        )
        cov = coverage_from_report(report, scope={_IDS: {"req-doc"}})
        row = next(r for r in cov.rows if r.source_id == "req-doc")
        self.assertEqual(row.status_for(_IDS), CoverageStatus.CHECKED_OK)

    def test_derive_scope_enables_real_checked_ok(self) -> None:
        report = _report(
            requirements=(ParsedRequirement(rule_id="r", source="spec"),),
            capabilities=ReportCapabilities(
                ifc_validation=CapabilityStatus(CapabilityState.OK),
                ifc_schema=CapabilityStatus(CapabilityState.OK),
            ),
        )
        cov = coverage_from_report(report, scope=derive_report_scope(report))
        row = next(r for r in cov.rows if r.source_id == "spec")
        self.assertEqual(row.status_for(_IFC), CoverageStatus.CHECKED_OK)

    def test_derive_scope_excludes_spatial_per_source(self) -> None:
        # SPATIAL (clash) is model/element-level, not per-document.
        report = _report(
            requirements=(ParsedRequirement(rule_id="r", source="spec"),),
            capabilities=ReportCapabilities(clash=CapabilityStatus(CapabilityState.OK)),
        )
        scope = derive_report_scope(report)
        self.assertNotIn(FindingCategory.SPATIAL, scope)
        row = next(
            r for r in coverage_from_report(report, scope=scope).rows if r.source_id == "spec"
        )
        self.assertEqual(row.status_for(FindingCategory.SPATIAL), CoverageStatus.NOT_CHECKED)

    def test_derive_scope_omits_family_when_capability_not_ok(self) -> None:
        report = _report(requirements=(ParsedRequirement(rule_id="r", source="spec"),))
        self.assertEqual(derive_report_scope(report), {})

    def test_ids_and_cross_document_are_not_auto_scoped(self) -> None:
        # Red Team HIGH-2/MEDIUM-1: an OK ids/section_pairing does not prove a requirement
        # source was processed -> must NOT auto-scope (stays NOT_CHECKED honestly).
        report = _report(
            requirements=(ParsedRequirement(rule_id="r", source="spec"),),
            capabilities=ReportCapabilities(
                ids=CapabilityStatus(CapabilityState.OK),
                section_pairing=CapabilityStatus(CapabilityState.OK),
            ),
        )
        scope = derive_report_scope(report)
        self.assertNotIn(_IDS, scope)
        self.assertNotIn(FindingCategory.CROSS_DOCUMENT, scope)
        row = next(
            r for r in coverage_from_report(report, scope=scope).rows if r.source_id == "spec"
        )
        self.assertEqual(row.status_for(_IDS), CoverageStatus.NOT_CHECKED)

    def test_drawing_annotation_only_source_not_ifc_scoped(self) -> None:
        # Red Team HIGH-1: the IFC validator skips drawing-annotation rules.
        report = _report(
            requirements=(
                ParsedRequirement(
                    rule_id="r", source="sheet.pdf", rule_scope=RuleScope.DRAWING_ANNOTATION
                ),
            ),
            capabilities=ReportCapabilities(
                ifc_validation=CapabilityStatus(CapabilityState.OK),
                ifc_schema=CapabilityStatus(CapabilityState.OK),
            ),
        )
        scope = derive_report_scope(report)
        self.assertEqual(scope.get(_IFC, set()), set())
        row = next(
            r for r in coverage_from_report(report, scope=scope).rows if r.source_id == "sheet.pdf"
        )
        self.assertEqual(row.status_for(_IFC), CoverageStatus.NOT_CHECKED)

    def test_asset_only_sheet_not_drawing_scoped(self) -> None:
        # Red Team MEDIUM-2: asset registers file presence, not OCR yield.
        report = _report(
            capabilities=ReportCapabilities(raster=CapabilityStatus(CapabilityState.OK)),
            drawing_assets=(DrawingAsset(asset_id="A1", sheet_id="A-101"),),
        )
        scope = derive_report_scope(report)
        self.assertEqual(scope.get(FindingCategory.DRAWING_VALIDATION, set()), set())
        row = next(
            r for r in coverage_from_report(report, scope=scope).rows if r.source_id == "A-101"
        )
        self.assertEqual(
            row.status_for(FindingCategory.DRAWING_VALIDATION), CoverageStatus.NOT_CHECKED
        )

    def test_offsheet_drawing_finding_blocks_sheet_checked_ok(self) -> None:
        # Deep Red Team: DRAWING findings are attributed to the requirement source, not the
        # sheet id -> a sheet must NOT read CHECKED_OK while such a finding exists off-sheet.
        region = DrawingRegionRef(
            sheet_id="sheet-12", bbox_xyxy=(0.0, 0.0, 1.0, 1.0), confidence=0.9, modality="ocr"
        )
        report = _report(
            issues=(_issue("spec.pdf", FindingCategory.DRAWING_VALIDATION),),
            capabilities=ReportCapabilities(raster=CapabilityStatus(CapabilityState.OK)),
            drawing_regions=(region,),
        )
        scope = derive_report_scope(report)
        self.assertNotIn(FindingCategory.DRAWING_VALIDATION, scope)
        row = next(
            r for r in coverage_from_report(report, scope=scope).rows if r.source_id == "sheet-12"
        )
        self.assertEqual(
            row.status_for(FindingCategory.DRAWING_VALIDATION), CoverageStatus.NOT_CHECKED
        )

    def test_package_without_mep_has_tz_gap_not_checked(self) -> None:
        """WP-R4 E2E: IFC-only package — MEP TZ gap stays not_checked, never no_findings."""
        report = _report(
            requirements=(ParsedRequirement(rule_id="r", source="model.ifc"),),
            capabilities=ReportCapabilities(clash=CapabilityStatus(CapabilityState.OK)),
        )
        payload = coverage_from_report(report, scope=derive_report_scope(report)).to_dict(
            report=report
        )
        mep_gap = next(g for g in payload["tz_gaps"] if g["gap_id"] == "mep_system_clash")
        self.assertEqual(mep_gap["status"], "not_checked")
        row = next(r for r in payload["sources"] if r["source_id"] == "model.ifc")
        spatial = row["operator_status"].get("spatial", "not_checked")
        self.assertNotEqual(spatial, "no_findings")
        self.assertEqual(spatial, "not_checked")

    def test_clean_sheet_checked_ok_without_offsheet_drawing_finding(self) -> None:
        region = DrawingRegionRef(
            sheet_id="sheet-12", bbox_xyxy=(0.0, 0.0, 1.0, 1.0), confidence=0.9, modality="ocr"
        )
        report = _report(
            capabilities=ReportCapabilities(raster=CapabilityStatus(CapabilityState.OK)),
            drawing_regions=(region,),
        )
        scope = derive_report_scope(report)
        row = next(
            r for r in coverage_from_report(report, scope=scope).rows if r.source_id == "sheet-12"
        )
        self.assertEqual(
            row.status_for(FindingCategory.DRAWING_VALIDATION), CoverageStatus.CHECKED_OK
        )


if __name__ == "__main__":
    unittest.main()
