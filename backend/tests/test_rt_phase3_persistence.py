"""Phase 3 persistence: commit gate, TTL cleanup, injected failure orphans."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from aerobim.domain.finding_provenance import ensure_finding_provenance
from aerobim.domain.models import (
    FindingCategory,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.domain.persistence import (
    ReportCommitState,
    is_report_reviewable,
)
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore
from aerobim.tools.reconcile_audit_orphans import reconcile_orphans


def _report(root: Path, report_id: str, *, created_at: str | None = None) -> ValidationReport:
    ifc = root / f"{report_id}.ifc"
    ifc.write_text("ISO-10303-21;", encoding="utf-8")
    issue = ensure_finding_provenance(
        ValidationIssue(
            rule_id="P3-1",
            severity=Severity.ERROR,
            message="x",
            category=FindingCategory.IFC_VALIDATION,
            source_id="persist-test",
            element_guid="guid-1",
        )
    )
    return ValidationReport(
        report_id=report_id,
        request_id="p3",
        ifc_path=ifc,
        created_at=created_at or datetime.now(tz=UTC).isoformat(),
        requirements=(),
        issues=(issue,),
        summary=ValidationSummary(0, 1, 1, 0, False),
    )


class PersistenceCommitGateTests(unittest.TestCase):
    def test_save_makes_reviewable_and_hides_uncommitted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = FilesystemAuditStore(root)
            report_id = "b" * 32
            store.save(_report(root, report_id))
            self.assertTrue(store.is_report_committed(report_id))
            self.assertTrue(store.is_report_reviewable(report_id))
            self.assertIsNotNone(store.get(report_id))

            # Simulate crash after JSON write before commit marker.
            store._commit_marker_path(report_id).unlink()
            self.assertFalse(is_report_reviewable(committed=False, report_json_exists=True))
            self.assertIsNone(store.get(report_id))
            self.assertEqual(store.list_reports(), [])

    def test_injected_commit_failure_records_orphan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = FilesystemAuditStore(root)
            report_id = "c" * 32
            with patch.object(
                store,
                "_write_commit_manifest",
                side_effect=OSError("disk full during commit"),
            ):
                with self.assertRaises(OSError):
                    store.save(_report(root, report_id))
            self.assertIn(report_id, store.list_orphan_report_ids())
            self.assertIsNone(store.get(report_id))
            result = reconcile_orphans(root, apply=True)
            self.assertEqual(result["records"][0]["status"], "cleaned_uncommitted")

    def test_ttl_deletes_commit_marker_and_review_events(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = FilesystemAuditStore(root, report_ttl_days=1)
            report_id = "d" * 32
            old = (datetime.now(tz=UTC) - timedelta(days=3)).isoformat()
            store.save(_report(root, report_id, created_at=old))
            events = root / "review-events"
            events.mkdir(parents=True)
            (events / f"{report_id}.jsonl").write_text("{}\n", encoding="utf-8")
            self.assertIsNone(store.get(report_id))
            self.assertFalse(store._report_json_path(report_id).exists())
            self.assertFalse(store._commit_marker_path(report_id).exists())
            self.assertFalse((events / f"{report_id}.jsonl").exists())

    def test_commit_manifest_has_schema_and_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = FilesystemAuditStore(root)
            report_id = "e" * 32
            store.save(_report(root, report_id))
            payload = json.loads(store._commit_marker_path(report_id).read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "1.0.0")
            self.assertEqual(payload["commit_state"], ReportCommitState.REVIEWABLE.value)
            self.assertTrue(payload["committed"])
            self.assertIn("committed_at", payload)


if __name__ == "__main__":
    unittest.main()
