"""DocumentIdentity + revision-merge guard tests."""

from __future__ import annotations

import unittest

from aerobim.domain.architecture import DocumentIdentity
from aerobim.domain.ingestion import (
    detect_revision_merge_conflicts,
    identity_from_requirement_source,
    revisions_conflict,
    stamp_requirement_source,
)
from aerobim.domain.models import ConflictKind, RequirementSource, SourceKind


class DocumentIdentityTests(unittest.TestCase):
    def test_identity_from_requirement_source(self) -> None:
        source = RequirementSource(
            text="wall height 3m",
            source_kind=SourceKind.STRUCTURED_TEXT,
            source_id="AR-101",
            revision="R2",
            stage="RD",
            doc_type="drawing",
            sha256="abc",
            doc_status="Shared",
        )
        identity = identity_from_requirement_source(source)
        self.assertEqual(
            identity,
            DocumentIdentity(
                source_id="AR-101",
                doc_type="drawing",
                revision="R2",
                status="Shared",
                stage="RD",
                sha256="abc",
            ),
        )

    def test_revisions_conflict_same_logical_document(self) -> None:
        left = DocumentIdentity(source_id="AR-101", doc_type="drawing", revision="R1")
        right = DocumentIdentity(source_id="AR-101", doc_type="drawing", revision="R2")
        self.assertTrue(revisions_conflict(left, right))

    def test_revisions_do_not_conflict_across_documents(self) -> None:
        left = DocumentIdentity(source_id="AR-101", doc_type="drawing", revision="R1")
        right = DocumentIdentity(source_id="AR-102", doc_type="drawing", revision="R2")
        self.assertFalse(revisions_conflict(left, right))

    def test_detect_revision_merge_emits_version_mismatch(self) -> None:
        sources = [
            stamp_requirement_source(
                RequirementSource(text="a", source_kind=SourceKind.STRUCTURED_TEXT),
                source_id="PKG-1",
                doc_type="specification",
                revision="A",
            ),
            stamp_requirement_source(
                RequirementSource(text="b", source_kind=SourceKind.TECHNICAL_SPECIFICATION),
                source_id="PKG-1",
                doc_type="specification",
                revision="B",
            ),
        ]
        issues = detect_revision_merge_conflicts(sources)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].conflict_kind, ConflictKind.VERSION_MISMATCH)
        self.assertEqual(issues[0].rule_id, "AEROBIM-REVISION-MERGE")

    def test_same_revision_is_not_a_conflict(self) -> None:
        sources = [
            RequirementSource(
                text="a",
                source_kind=SourceKind.STRUCTURED_TEXT,
                source_id="PKG-1",
                doc_type="specification",
                revision="A",
            ),
            RequirementSource(
                text="b",
                source_kind=SourceKind.TECHNICAL_SPECIFICATION,
                source_id="PKG-1",
                doc_type="specification",
                revision="A",
            ),
        ]
        self.assertEqual(detect_revision_merge_conflicts(sources), [])


if __name__ == "__main__":
    unittest.main()
