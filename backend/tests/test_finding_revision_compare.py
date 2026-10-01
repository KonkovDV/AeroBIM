"""Unit tests for cross-revision finding comparison."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.finding_revision_compare import (
    FindingRevisionStatus,
    compare_findings_across_revisions,
    export_finding_revision_delta_document,
)
from aerobim.domain.models import FindingCategory, Severity, ValidationIssue
from aerobim.tools.export_finding_revision_delta import main


class FindingRevisionCompareTests(unittest.TestCase):
    def test_match_by_finding_id_not_message(self) -> None:
        previous = [
            ValidationIssue(
                rule_id="R1",
                severity=Severity.WARNING,
                message="old wording A",
                finding_id="abc123",
                element_guid="GUID-1",
                source_id="doc-a",
                category=FindingCategory.IFC_VALIDATION,
            )
        ]
        current = [
            ValidationIssue(
                rule_id="R1",
                severity=Severity.WARNING,
                message="completely different message text",
                finding_id="abc123",
                element_guid="GUID-1",
                source_id="doc-a",
                category=FindingCategory.IFC_VALIDATION,
            )
        ]
        deltas = compare_findings_across_revisions(previous, current)
        self.assertEqual(len(deltas), 1)
        self.assertEqual(deltas[0].status, FindingRevisionStatus.UNCHANGED)
        self.assertEqual(deltas[0].match_basis, "finding_id")

    def test_new_resolved_changed_regressed(self) -> None:
        previous = [
            {
                "finding_id": "keep",
                "rule_id": "R-KEEP",
                "severity": "warning",
                "observed_value": "1",
            },
            {
                "finding_id": "gone",
                "rule_id": "R-GONE",
                "severity": "error",
            },
            {
                "rule_id": "R-GUID",
                "element_guid": "G-1",
                "severity": "warning",
                "observed_value": "a",
            },
        ]
        current = [
            {
                "finding_id": "keep",
                "rule_id": "R-KEEP",
                "severity": "warning",
                "observed_value": "1",
            },
            {
                "finding_id": "fresh",
                "rule_id": "R-NEW",
                "severity": "error",
            },
            {
                "rule_id": "R-GUID",
                "element_guid": "G-1",
                "severity": "error",
                "observed_value": "b",
            },
        ]
        deltas = compare_findings_across_revisions(previous, current)
        by_status = {delta.status: delta for delta in deltas}
        self.assertEqual(by_status[FindingRevisionStatus.UNCHANGED].match_key, "finding_id:keep")
        self.assertEqual(by_status[FindingRevisionStatus.RESOLVED].match_key, "finding_id:gone")
        self.assertEqual(by_status[FindingRevisionStatus.NEW].match_key, "finding_id:fresh")
        self.assertEqual(
            by_status[FindingRevisionStatus.REGRESSED].match_basis, "rule_id+element_guid"
        )

    def test_document_identity_match_and_cannot_match_ambiguous(self) -> None:
        previous = [
            {
                "rule_id": "R-DOC",
                "source_id": "sheet-1",
                "target_ref": "APT-01",
                "severity": "warning",
                "observed_value": "old",
            },
            {
                "rule_id": "R-AMB",
                "element_guid": "SAME",
                "severity": "warning",
                "observed_value": "1",
            },
            {
                "rule_id": "R-AMB",
                "element_guid": "SAME",
                "severity": "warning",
                "observed_value": "2",
            },
        ]
        current = [
            {
                "rule_id": "R-DOC",
                "source_id": "sheet-1",
                "target_ref": "APT-01",
                "severity": "warning",
                "observed_value": "x",
            },
            {
                "rule_id": "R-AMB",
                "element_guid": "SAME",
                "severity": "error",
            },
        ]
        deltas = compare_findings_across_revisions(previous, current)
        statuses = [delta.status for delta in deltas]
        self.assertIn(FindingRevisionStatus.CHANGED, statuses)
        self.assertGreaterEqual(statuses.count(FindingRevisionStatus.CANNOT_MATCH), 2)
        doc_delta = next(
            delta for delta in deltas if delta.match_basis == "rule_id+document_identity"
        )
        self.assertEqual(doc_delta.status, FindingRevisionStatus.CHANGED)

    def test_export_document_and_cli(self) -> None:
        deltas = compare_findings_across_revisions(
            [{"finding_id": "a", "rule_id": "R", "severity": "error"}],
            [{"finding_id": "a", "rule_id": "R", "severity": "error"}],
        )
        document = export_finding_revision_delta_document(
            previous_revision="r1",
            current_revision="r2",
            deltas=deltas,
        )
        self.assertEqual(document["schema_version"], "1.0.0")
        self.assertIn("not a customer revision pack", document["claim_boundary"])
        self.assertEqual(document["counts"]["unchanged"], 1)

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            prev = root / "prev.json"
            curr = root / "curr.json"
            out = root / "delta.json"
            prev.write_text(
                json.dumps(
                    {
                        "revision": "r1",
                        "issues": [
                            {
                                "finding_id": "x",
                                "rule_id": "R",
                                "severity": "warning",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            curr.write_text(
                json.dumps(
                    {
                        "revision": "r2",
                        "issues": [
                            {
                                "finding_id": "x",
                                "rule_id": "R",
                                "severity": "error",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                main(["--previous", str(prev), "--current", str(curr), "--output", str(out)]),
                0,
            )
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["counts"]["regressed"], 1)


if __name__ == "__main__":
    unittest.main()
