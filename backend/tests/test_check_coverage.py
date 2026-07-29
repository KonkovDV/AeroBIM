"""Check-coverage map: per-source honesty — 'no findings' is NOT 'not checked' (P0).

Ключевой инвариант (anti-silent-PASS): источник без находок получает CHECKED_OK
ТОЛЬКО если проверка реально шла (capability OK); иначе NOT_CHECKED. Карта
verdict-neutral: не содержит и не выставляет вердикт.
"""

from __future__ import annotations

import json
import unittest

from aerobim.domain.check_coverage import (
    CheckCoverageMap,
    CoverageStatus,
    build_check_coverage,
)
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    FindingCategory,
    ReportCapabilities,
    Severity,
    ValidationIssue,
)

_IFC = FindingCategory.IFC_VALIDATION


def _issue(
    source_id: str, category: FindingCategory, *, origin: str = "deterministic"
) -> ValidationIssue:
    return ValidationIssue(
        rule_id="R",
        severity=Severity.ERROR,
        message="m",
        category=category,
        source_id=source_id,
        origin=origin,  # type: ignore[arg-type]
    )


def _caps(state: CapabilityState, reason: str | None = None) -> ReportCapabilities:
    return ReportCapabilities(ifc_validation=CapabilityStatus(state, reason))


class CheckCoverageTests(unittest.TestCase):
    def test_deterministic_finding_is_checked_findings(self) -> None:
        cov = build_check_coverage(
            source_ids=["a"], issues=[_issue("a", _IFC)], capabilities=_caps(CapabilityState.OK)
        )
        self.assertEqual(cov.rows[0].status_for(_IFC), CoverageStatus.CHECKED_FINDINGS)

    def test_advisory_only_requires_expert(self) -> None:
        cov = build_check_coverage(
            source_ids=["a"],
            issues=[_issue("a", _IFC, origin="advisory")],
            capabilities=_caps(CapabilityState.OK),
        )
        self.assertEqual(cov.rows[0].status_for(_IFC), CoverageStatus.REQUIRES_EXPERT)

    def test_no_findings_capability_ok_is_checked_ok(self) -> None:
        cov = build_check_coverage(
            source_ids=["a"], issues=[], capabilities=_caps(CapabilityState.OK)
        )
        self.assertEqual(cov.rows[0].status_for(_IFC), CoverageStatus.CHECKED_OK)

    def test_no_findings_not_run_is_not_checked_not_silent_ok(self) -> None:
        # ANTI-SILENT-PASS: default ifc_validation is SKIPPED -> must be NOT_CHECKED.
        cov = build_check_coverage(source_ids=["a"], issues=[], capabilities=ReportCapabilities())
        self.assertEqual(cov.rows[0].status_for(_IFC), CoverageStatus.NOT_CHECKED)

    def test_failed_capability_is_insufficient_data(self) -> None:
        cov = build_check_coverage(
            source_ids=["a"], issues=[], capabilities=_caps(CapabilityState.FAILED, "boom")
        )
        self.assertEqual(cov.rows[0].status_for(_IFC), CoverageStatus.INSUFFICIENT_DATA)

    def test_missing_capability_is_not_checked(self) -> None:
        cov = build_check_coverage(
            source_ids=["a"], issues=[], capabilities=_caps(CapabilityState.MISSING, "gap")
        )
        self.assertEqual(cov.rows[0].status_for(_IFC), CoverageStatus.NOT_CHECKED)

    def test_verdict_neutral_no_verdict_fields(self) -> None:
        cov = build_check_coverage(source_ids=["a"], issues=[], capabilities=ReportCapabilities())
        self.assertIsInstance(cov, CheckCoverageMap)
        self.assertFalse(hasattr(cov, "passed"))
        self.assertFalse(hasattr(cov, "summary_passed"))
        record = cov.to_dict()
        self.assertNotIn("passed", record)
        self.assertNotIn("summary_passed", record)

    def test_to_dict_is_json_safe_and_dedupes_sources(self) -> None:
        cov = build_check_coverage(
            source_ids=["a", "a", "b", ""],
            issues=[_issue("a", _IFC)],
            capabilities=_caps(CapabilityState.OK),
        )
        record = cov.to_dict()
        json.dumps(record)  # JSON-safe
        self.assertEqual(len(record["sources"]), 2)  # deduped + empty dropped
        self.assertEqual(record["sources"][0]["families"][_IFC.value], "checked_findings")
        self.assertIn(CoverageStatus.CHECKED_FINDINGS.value, record["summary"])

    def test_every_family_present_per_source(self) -> None:
        cov = build_check_coverage(source_ids=["a"], issues=[], capabilities=ReportCapabilities())
        self.assertEqual(len(cov.rows[0].families), len(list(FindingCategory)))


if __name__ == "__main__":
    unittest.main()
