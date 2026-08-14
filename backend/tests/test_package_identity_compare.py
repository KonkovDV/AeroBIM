"""Package-vs-package document identity compare (TZ row 28 fixture path)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.architecture import DocumentIdentity
from aerobim.domain.ingestion import (
    PACKAGE_IDENTITY_CLAIM_BOUNDARY,
    compare_package_document_identities,
    identities_from_mapping,
)
from aerobim.domain.models import ConflictKind
from aerobim.tools.compare_package_identities import compare_payload

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / "samples" / "packages" / "identity-compare-pd-rd.json"


class PackageIdentityCompareTests(unittest.TestCase):
    def test_matching_identities_emit_no_issues(self) -> None:
        row = DocumentIdentity(
            source_id="PZ",
            doc_type="explanatory_note",
            stage="PD",
            revision="R1",
        )
        self.assertEqual(compare_package_document_identities([row], [row]), [])

    def test_stage_revision_and_type_mismatches(self) -> None:
        previous = [
            DocumentIdentity(
                source_id="PZ",
                doc_type="explanatory_note",
                stage="PD",
                revision="R1",
            ),
            DocumentIdentity(source_id="AR-101", doc_type="drawing", stage="PD", revision="R1"),
        ]
        current = [
            DocumentIdentity(
                source_id="PZ",
                doc_type="explanatory_note",
                stage="RD",
                revision="R2",
            ),
            DocumentIdentity(source_id="AR-101", doc_type="plan", stage="PD", revision="R1"),
        ]
        issues = compare_package_document_identities(previous, current)
        kinds = {issue.conflict_kind for issue in issues}
        self.assertEqual(
            kinds,
            {
                ConflictKind.STAGE_MISMATCH,
                ConflictKind.VERSION_MISMATCH,
                ConflictKind.DOC_TYPE_MISMATCH,
            },
        )
        self.assertTrue(all(PACKAGE_IDENTITY_CLAIM_BOUNDARY in issue.message for issue in issues))

    def test_added_and_removed_documents(self) -> None:
        previous = [DocumentIdentity(source_id="KZH-01", doc_type="calculation")]
        current = [DocumentIdentity(source_id="IOS-01", doc_type="specification")]
        issues = compare_package_document_identities(previous, current)
        rules = {issue.rule_id for issue in issues}
        self.assertEqual(rules, {"AEROBIM-PACKAGE-DOC-REMOVED", "AEROBIM-PACKAGE-DOC-ADDED"})

    def test_committed_fixture_via_cli_payload(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        document = compare_payload(payload)
        self.assertFalse(document["cde_version_management"])
        self.assertFalse(document["closes_rt001"])
        self.assertGreaterEqual(document["error_count"], 3)
        rule_ids = {row["rule_id"] for row in document["issues"]}
        self.assertIn("AEROBIM-PACKAGE-STAGE-MISMATCH", rule_ids)
        self.assertIn("AEROBIM-PACKAGE-VERSION-MISMATCH", rule_ids)
        self.assertIn("AEROBIM-PACKAGE-DOC-TYPE-MISMATCH", rule_ids)
        self.assertIn("AEROBIM-PACKAGE-DOC-REMOVED", rule_ids)
        self.assertIn("AEROBIM-PACKAGE-DOC-ADDED", rule_ids)
        mapped = identities_from_mapping(payload["previous"])
        self.assertEqual(mapped[0].source_id, "PZ")

    def test_duplicate_source_id_is_ambiguous(self) -> None:
        previous = [
            DocumentIdentity(source_id="PZ", doc_type="explanatory_note", revision="R1"),
            DocumentIdentity(source_id="PZ", doc_type="explanatory_note", revision="R2"),
        ]
        issues = compare_package_document_identities(previous, previous[:1])
        self.assertTrue(any(issue.rule_id == "AEROBIM-PACKAGE-DOC-DUPLICATE" for issue in issues))
        self.assertTrue(
            any(issue.conflict_kind is ConflictKind.AMBIGUOUS_MAPPING for issue in issues)
        )

    def test_identical_casefold_stage_is_not_mismatch(self) -> None:
        previous = [DocumentIdentity(source_id="AR-101", doc_type="Drawing", stage="pd")]
        current = [DocumentIdentity(source_id="AR-101", doc_type="drawing", stage="PD")]
        issues = compare_package_document_identities(previous, current)
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
