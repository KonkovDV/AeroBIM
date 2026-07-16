"""BCF contract tests: two independent consumers must agree on GUID/title/viewpoint."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aerobim.domain.models import (
    ClashResult,
    FindingCategory,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.infrastructure.adapters.bcf3_exporter import export_bcf3
from aerobim.infrastructure.adapters.bcf_consumers import (
    consume_bcf3_zip,
    consume_bcf21_zip,
    verify_bcf_zip_structure,
)
from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf
from aerobim.tools.verify_bcf_structural_handoff import build_bcf_structural_handoff_evidence


def _report() -> ValidationReport:
    issues = (
        ValidationIssue(
            rule_id="IDS-WallHeight",
            severity=Severity.ERROR,
            message="Wall height below minimum",
            category=FindingCategory.IDS_VALIDATION,
            element_guid="2O2Fr$t4X7Zf8NOew3FLOH",
        ),
    )
    return ValidationReport(
        report_id=uuid4().hex,
        request_id="req-bcf-contract",
        ifc_path=Path("contract.ifc"),
        created_at=datetime.now(tz=UTC).isoformat(),
        requirements=(),
        issues=issues,
        summary=ValidationSummary(
            requirement_count=0,
            issue_count=1,
            error_count=1,
            warning_count=0,
            passed=False,
        ),
        clash_results=(
            ClashResult(
                element_a_guid="clash-a",
                element_b_guid="clash-b",
                clash_type="hard",
                distance=0.02,
                description="Hard clash",
            ),
        ),
    )


class BcfMultiConsumerContractTests(unittest.TestCase):
    def test_bcf21_consumer_extracts_guid_title_viewpoint(self) -> None:
        archive = export_bcf(_report())
        topics = consume_bcf21_zip(archive)
        self.assertGreaterEqual(len(topics), 1)
        for topic in topics:
            self.assertTrue(topic.topic_guid)
            self.assertTrue(topic.title)
            self.assertTrue(topic.has_viewpoint)

    def test_bcf3_consumer_extracts_guid_title_viewpoint(self) -> None:
        archive = export_bcf3(_report())
        topics = consume_bcf3_zip(archive)
        self.assertGreaterEqual(len(topics), 1)
        for topic in topics:
            self.assertTrue(topic.topic_guid)
            self.assertTrue(topic.title)
            self.assertTrue(topic.has_viewpoint)

    def test_two_consumers_agree_on_topic_count_for_same_report(self) -> None:
        report = _report()
        topics_21 = consume_bcf21_zip(export_bcf(report))
        topics_30 = consume_bcf3_zip(export_bcf3(report))
        self.assertEqual(len(topics_21), len(topics_30))
        titles_21 = sorted(t.title for t in topics_21)
        titles_30 = sorted(t.title for t in topics_30)
        self.assertEqual(titles_21, titles_30)

    def test_structural_verifier_accepts_bcf21_and_bcf3(self) -> None:
        report = _report()
        for archive in (export_bcf(report), export_bcf3(report)):
            result = verify_bcf_zip_structure(archive)
            self.assertTrue(result.ok, msg=result.errors)
            self.assertTrue(result.sha256)
            self.assertGreaterEqual(result.topic_count, 1)
            self.assertEqual(result.xsd_status, "not_configured")

    def test_structural_handoff_evidence_keeps_cde_not_verified(self) -> None:
        payload = build_bcf_structural_handoff_evidence()
        self.assertTrue(payload["structural_ok"])
        self.assertEqual(payload["cde_import"]["status"], "NOT_VERIFIED")
        self.assertEqual(payload["claim_level"], "structural_only")


if __name__ == "__main__":
    unittest.main()
