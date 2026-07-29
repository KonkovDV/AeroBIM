"""Revision diff: finding + element delta between two report revisions (P1).

Verdict-neutral observability. 'no_longer_reported' must NOT claim 'resolved';
finding_id is the stable key; output is deterministic (sorted) and JSON-safe.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.models import (
    FindingCategory,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.domain.revision_diff import compare_report_revisions


def _issue(
    rule_id: str,
    *,
    category: FindingCategory = FindingCategory.IFC_VALIDATION,
    element_guid: str | None = None,
    finding_id: str | None = None,
) -> ValidationIssue:
    return ValidationIssue(
        rule_id=rule_id,
        severity=Severity.ERROR,
        message="m",
        category=category,
        element_guid=element_guid,
        finding_id=finding_id,
    )


def _report(
    report_id: str, issues: list[ValidationIssue], *, revision: str | None = None
) -> ValidationReport:
    return ValidationReport(
        report_id=report_id,
        request_id="req",
        ifc_path=Path("m.ifc"),
        created_at="2026-07-29T00:00:00Z",
        requirements=(),
        issues=tuple(issues),
        summary=ValidationSummary(0, len(issues), 0, 0, True),
        revision=revision,
    )


class RevisionDiffTests(unittest.TestCase):
    def test_newly_reported(self) -> None:
        diff = compare_report_revisions(
            _report("old", []), _report("new", [_issue("R1", finding_id="f1")])
        )
        self.assertEqual(diff.summary()["newly_reported"], 1)
        self.assertEqual(diff.summary()["no_longer_reported"], 0)

    def test_no_longer_reported_is_not_claimed_resolved(self) -> None:
        diff = compare_report_revisions(
            _report("old", [_issue("R1", finding_id="f1")]), _report("new", [])
        )
        self.assertEqual(diff.summary()["no_longer_reported"], 1)
        self.assertIn("does NOT claim 'resolved'", diff.to_dict()["note"])

    def test_still_reported(self) -> None:
        diff = compare_report_revisions(
            _report("old", [_issue("R1", finding_id="f1")]),
            _report("new", [_issue("R1", finding_id="f1")]),
        )
        self.assertEqual(diff.summary()["still_reported"], 1)
        self.assertEqual(diff.summary()["newly_reported"], 0)

    def test_element_guid_delta(self) -> None:
        diff = compare_report_revisions(
            _report("old", [_issue("R1", element_guid="G-OLD", finding_id="f1")]),
            _report("new", [_issue("R1", element_guid="G-NEW", finding_id="f2")]),
        )
        self.assertIn("G-OLD", diff.elements_only_in_old)
        self.assertIn("G-NEW", diff.elements_only_in_new)

    def test_finding_id_distinguishes_same_rule(self) -> None:
        diff = compare_report_revisions(
            _report("old", []),
            _report("new", [_issue("R1", finding_id="f1"), _issue("R1", finding_id="f2")]),
        )
        self.assertEqual(diff.summary()["newly_reported"], 2)

    def test_verdict_neutral_json_safe_with_revisions(self) -> None:
        diff = compare_report_revisions(
            _report("old", [], revision="01"),
            _report("new", [_issue("R1", finding_id="f1")], revision="02"),
        )
        record = diff.to_dict()
        json.dumps(record)
        self.assertNotIn('"passed"', json.dumps(record))
        self.assertEqual(record["old_revision"], "01")
        self.assertEqual(record["new_revision"], "02")

    def test_output_is_sorted_deterministic(self) -> None:
        diff = compare_report_revisions(
            _report("old", []),
            _report("new", [_issue("Rb", finding_id="fb"), _issue("Ra", finding_id="fa")]),
        )
        self.assertEqual(list(diff.newly_reported), sorted(diff.newly_reported))


if __name__ == "__main__":
    unittest.main()
