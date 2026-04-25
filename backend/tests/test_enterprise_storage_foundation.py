from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from aerobim.domain.models import ValidationReport, ValidationSummary
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore
from aerobim.infrastructure.adapters.local_object_store import LocalObjectStore


def _make_report(
    report_id: str,
    *,
    ifc_path: Path,
    created_at: str | None = None,
) -> ValidationReport:
    return ValidationReport(
        report_id=report_id,
        request_id=f"req-{report_id[:8]}",
        ifc_path=ifc_path,
        created_at=created_at or datetime.now(tz=UTC).isoformat(),
        requirements=(),
        issues=(),
        summary=ValidationSummary(
            requirement_count=0,
            issue_count=0,
            error_count=0,
            warning_count=0,
            passed=True,
        ),
    )


class LocalObjectStoreTests(unittest.TestCase):
    def test_put_get_delete_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalObjectStore(Path(tmpdir))

            key = store.put_bytes("drawing-assets/report-1/preview.png", b"png-bytes")
            self.assertEqual(store.get_bytes(key), b"png-bytes")
            self.assertIsNotNone(store.presign_get(key))

            store.delete(key)
            self.assertIsNone(store.get_bytes(key))


class FilesystemAuditStoreEnterpriseFoundationTests(unittest.TestCase):
    def test_save_copies_ifc_source_into_object_store_and_roundtrips_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir)
            ifc_path = storage_dir / "model.ifc"
            ifc_path.write_text("ISO-10303-21;\nEND-ISO-10303-21;\n", encoding="utf-8")

            store = FilesystemAuditStore(storage_dir)
            report = _make_report("c" * 32, ifc_path=ifc_path)

            store.save(report)
            loaded = store.get(report.report_id)

            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertIsNotNone(loaded.ifc_object_key)
            self.assertTrue((storage_dir / str(loaded.ifc_object_key)).exists())

    def test_get_prunes_reports_older_than_ttl(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir)
            ifc_path = storage_dir / "expired.ifc"
            ifc_path.write_text("ISO-10303-21;\nEND-ISO-10303-21;\n", encoding="utf-8")

            store = FilesystemAuditStore(storage_dir, report_ttl_days=1)
            expired_report = _make_report(
                "d" * 32,
                ifc_path=ifc_path,
                created_at=(datetime.now(tz=UTC) - timedelta(days=3)).isoformat(),
            )
            store.save(expired_report)

            self.assertIsNone(store.get(expired_report.report_id))
            self.assertEqual(store.list_reports(), [])
            self.assertFalse(
                (storage_dir / "reports" / f"{expired_report.report_id}.json").exists()
            )