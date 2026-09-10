"""WP-R9: rejected findings leave the pack-finding list but stay in the report."""

from __future__ import annotations

import io
import unittest
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aerobim.domain.finding_provenance import ensure_finding_provenance
from aerobim.domain.models import (
    FindingCategory,
    GeneratedRemark,
    ReviewEvent,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.domain.review_projection import review_partition, review_partition_of
from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf
from aerobim.presentation.http.report_html import render_report_html
from aerobim.presentation.http.report_pdf import render_report_pdf_bytes


def _issue_dict(**overrides: object) -> dict:
    item: dict[str, object] = {
        "rule_id": "REQ-FIRE-001",
        "severity": "error",
        "message": "Property Pset_WallCommon.FireRating does not match the expected value",
        "category": "ids-validation",
        "priority": 40,
        "finding_id": "fid-1",
        "source_id": "ids",
        "origin": "deterministic",
        "element_guid": "guid-wall",
        "target_ref": "Wall-01",
        "evidence_refs": ["guid-wall"],
        "remark": {
            "essence": "Стена не соответствует",
            "title": "Замечание по модели: Стена",
            "body": "T0",
            "clause_cite": "СП 2.13130 п. 5.4.3",
            "clause_bound": True,
            "location_line": "этаж 3",
        },
    }
    item.update(overrides)
    return item


class ReviewStateExportTests(unittest.TestCase):
    def test_rejected_finding_not_in_pack_findings_section(self) -> None:
        rejected = _issue_dict(
            review={
                "state": "rejected",
                "actor": "expert-1",
                "effective_text": "нет",
                "machine_text": "T0",
            }
        )
        html = render_report_html(
            "r" * 32,
            {
                "summary": {
                    "passed": False,
                    "issue_count": 1,
                    "error_count": 1,
                    "warning_count": 0,
                    "requirement_count": 0,
                },
                "issues": [rejected],
            },
        )
        pack = html[html.find("id='layer-pack_finding'") : html.find("id='layer-coverage_note'")]
        self.assertNotIn("Стена не соответствует", pack)
        self.assertIn("id='layer-rejected'", html)
        self.assertIn("Отклонено экспертом", html)
        self.assertIn("expert-1", html)

    def test_rejected_finding_still_present_in_rejected_section(self) -> None:
        rejected = _issue_dict(
            review={"state": "rejected", "actor": "expert-1", "machine_text": "T0"}
        )
        html = render_report_html(
            "r" * 32,
            {
                "summary": {
                    "passed": False,
                    "issue_count": 1,
                    "error_count": 1,
                    "warning_count": 0,
                    "requirement_count": 0,
                },
                "issues": [rejected],
            },
        )
        rejected_html = html[html.find("id='layer-rejected'") :]
        self.assertIn("Стена не соответствует", rejected_html)
        self.assertIn("всего машинных записей: 1", html)

    def test_edited_text_becomes_primary_and_machine_moves_to_audit(self) -> None:
        edited = _issue_dict(
            review={
                "state": "edited",
                "effective_text": "Текст эксперта про стену",
                "machine_text": "T0",
            }
        )
        html = render_report_html(
            "r" * 32,
            {
                "summary": {
                    "passed": False,
                    "issue_count": 1,
                    "error_count": 1,
                    "warning_count": 0,
                    "requirement_count": 0,
                },
                "issues": [edited],
            },
        )
        pack = html[html.find("id='layer-pack_finding'") : html.find("id='layer-coverage_note'")]
        self.assertIn("Текст эксперта про стену", pack)
        self.assertIn("machine=T0", pack)
        self.assertIn("текст эксперта", pack)

    def test_accepted_finding_marked_confirmed(self) -> None:
        accepted = _issue_dict(
            review={"state": "accepted", "actor": "expert-1", "machine_text": "T0"}
        )
        html = render_report_html(
            "r" * 32,
            {
                "summary": {
                    "passed": False,
                    "issue_count": 1,
                    "error_count": 1,
                    "warning_count": 0,
                    "requirement_count": 0,
                },
                "issues": [accepted],
            },
        )
        pack = html[html.find("id='layer-pack_finding'") : html.find("id='layer-coverage_note'")]
        self.assertIn("подтверждено экспертом", pack)
        self.assertIn("подтверждено экспертом: 1", html)

    def test_bcf_export_respects_rejection(self) -> None:
        issue = ensure_finding_provenance(
            ValidationIssue(
                rule_id="FIRE-1",
                severity=Severity.ERROR,
                message="mismatch",
                category=FindingCategory.IFC_VALIDATION,
                element_guid="guid-wall",
                remark=GeneratedRemark(title="m", body="T0"),
                origin="deterministic",
            )
        )
        report = ValidationReport(
            report_id=uuid4().hex,
            request_id="bcf-rej",
            ifc_path=Path("m.ifc"),
            created_at=datetime.now(tz=UTC).isoformat(),
            requirements=(),
            issues=(issue,),
            summary=ValidationSummary(0, 1, 1, 0, False),
        )
        events = (
            ReviewEvent(
                event_id="e-rej",
                report_id=report.report_id,
                event_type="rejected",
                created_at="2026-09-09T00:00:00+00:00",
                issue_rule_id=issue.rule_id,
                finding_id=issue.finding_id,
                resulting_state="rejected",
                actor="expert-1",
            ),
        )
        opened = export_bcf(report)
        rejected = export_bcf(report, review_events=events)
        self.assertGreater(len(zipfile.ZipFile(io.BytesIO(opened)).namelist()), 1)
        names = zipfile.ZipFile(io.BytesIO(rejected)).namelist()
        markup = [name for name in names if name.endswith("/markup.bcf")]
        self.assertEqual(markup, [])

    def test_review_state_does_not_change_summary_passed(self) -> None:
        issues = [
            _issue_dict(review={"state": "rejected"}),
            _issue_dict(finding_id="fid-2", review={"state": "accepted"}),
        ]
        html = render_report_html(
            "r" * 32,
            {
                "summary": {
                    "passed": False,
                    "issue_count": 2,
                    "error_count": 2,
                    "warning_count": 0,
                    "requirement_count": 0,
                },
                "issues": issues,
            },
        )
        self.assertIn("summary.passed=false", html)
        buckets = review_partition(issues)
        self.assertEqual(len(buckets["rejected"]), 1)
        self.assertEqual(len(buckets["confirmed"]), 1)
        self.assertEqual(review_partition_of(issues[0]), "rejected")

    def test_pdf_rejected_heading_present(self) -> None:
        pdf = render_report_pdf_bytes(
            "r" * 32,
            {
                "summary": {
                    "passed": False,
                    "issue_count": 1,
                    "error_count": 1,
                    "warning_count": 0,
                },
                "issues": [_issue_dict(review={"state": "rejected", "machine_text": "T0"})],
                "coverage": {},
            },
        )
        from test_report_pdf_coverage import extract_pdf_text

        text = extract_pdf_text(pdf)
        self.assertIn("Отклонено экспертом", text)
        self.assertIn("FAILED", text)


if __name__ == "__main__":
    unittest.main()
