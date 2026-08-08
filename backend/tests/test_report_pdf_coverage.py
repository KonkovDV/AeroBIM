"""WP-R4: PDF export places coverage map on the first page."""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.domain.check_coverage import coverage_from_report
from aerobim.domain.models import (
    ParsedRequirement,
    ValidationReport,
    ValidationSummary,
)
from aerobim.presentation.http.report_pdf import render_report_pdf_bytes


class ReportPdfCoverageTests(unittest.TestCase):
    def test_pdf_starts_with_coverage_block(self) -> None:
        report = ValidationReport(
            report_id="r1",
            request_id="req",
            ifc_path=Path("m.ifc"),
            created_at="2026-08-08T00:00:00Z",
            requirements=(ParsedRequirement(rule_id="r", source="spec.pdf"),),
            issues=(),
            summary=ValidationSummary(
                requirement_count=1,
                issue_count=0,
                error_count=0,
                warning_count=0,
                passed=True,
            ),
        )
        data = {
            "summary": {
                "passed": True,
                "issue_count": 0,
                "error_count": 0,
                "warning_count": 0,
                "requirement_count": 1,
            },
            "issues": [],
            "coverage": coverage_from_report(report).to_dict(report=report),
        }
        pdf = render_report_pdf_bytes("r1", data)
        self.assertTrue(pdf.startswith(b"%PDF"))
        # Coverage strings are embedded in first content stream (page 1).
        blob = pdf.decode("latin-1", errors="replace")
        cov_pos = blob.find("CHECK COVERAGE MAP")
        self.assertGreater(cov_pos, 0)
        self.assertIn("not_checked", blob)
        self.assertIn("MEP", blob)
