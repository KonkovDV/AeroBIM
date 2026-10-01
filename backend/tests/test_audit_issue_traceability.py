"""Tests for issue traceability audit tool."""

from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import (
    FindingCategory,
    ProblemZone,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.tools.audit_issue_traceability import audit_report_traceability


class AuditIssueTraceabilityTests(unittest.TestCase):
    def test_traceability_ratio_on_stored_report(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            storage = Path(tmp) / "reports"
            settings = replace(Settings.from_env(), storage_dir=storage)
            container = bootstrap_container(settings)
            store = container.resolve(Tokens.AUDIT_REPORT_STORE)
            report_id = uuid4().hex
            report = ValidationReport(
                report_id=report_id,
                request_id="trace-test",
                ifc_path=Path("samples/ifc/wall-fire-rating-rei60.ifc"),
                created_at="2026-05-21T00:00:00+00:00",
                requirements=(),
                issues=(
                    ValidationIssue(
                        rule_id="T-001",
                        severity=Severity.ERROR,
                        message="m",
                        category=FindingCategory.IFC_VALIDATION,
                        element_guid="guid-1",
                    ),
                    ValidationIssue(
                        rule_id="T-002",
                        severity=Severity.WARNING,
                        message="m2",
                        category=FindingCategory.DRAWING_VALIDATION,
                        problem_zone=ProblemZone(sheet_id="A-1"),
                    ),
                    ValidationIssue(
                        rule_id="T-003",
                        severity=Severity.INFO,
                        message="no anchor",
                        category=FindingCategory.IFC_VALIDATION,
                    ),
                ),
                summary=ValidationSummary(
                    requirement_count=0,
                    issue_count=3,
                    error_count=1,
                    warning_count=1,
                    passed=False,
                ),
            )
            store.save(report)
            payload = audit_report_traceability(report_id, storage_dir=storage)
            self.assertEqual(payload["traceable_count"], 2)
            self.assertAlmostEqual(payload["traceability_ratio"], 2 / 3, places=3)
            self.assertFalse(payload["pass_threshold_0_90"])


if __name__ == "__main__":
    unittest.main()
