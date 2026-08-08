"""WP-R4: exported HTML places coverage map before issue sections."""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.domain.check_coverage import coverage_from_report
from aerobim.domain.models import (
    ParsedRequirement,
    ValidationReport,
    ValidationSummary,
)
from aerobim.presentation.http.report_html import render_report_html


class ReportHtmlCoverageTests(unittest.TestCase):
    def test_coverage_section_precedes_issues(self) -> None:
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
            "issues": [
                {
                    "category": "ifc-validation",
                    "severity": "error",
                    "rule_id": "R",
                    "message": "x",
                    "priority": 10,
                }
            ],
            "coverage": coverage_from_report(report).to_dict(report=report),
        }
        html = render_report_html("r1", data)
        cov_pos = html.find("Карта покрытия проверок")
        issue_pos = html.find("IFC Model Validation")
        self.assertGreater(cov_pos, 0)
        self.assertGreater(issue_pos, cov_pos)
        self.assertIn("not_checked", html)
        self.assertIn("Пересечения инженерных систем", html)
