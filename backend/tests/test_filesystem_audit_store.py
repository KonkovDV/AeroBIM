from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.domain.models import ValidationReport
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore


def _make_report(
    report_id: str = "rpt-001", passed: bool = True, issue_count: int = 0
) -> ValidationReport:
    from aerobim.domain.models import ClashResult, ValidationSummary

    return ValidationReport(
        report_id=report_id,
        request_id="req-001",
        ifc_path=Path("sample.ifc"),
        created_at="2026-04-09T12:00:00Z",
        requirements=(),
        issues=(),
        summary=ValidationSummary(
            requirement_count=0,
            issue_count=issue_count,
            error_count=issue_count,
            warning_count=0,
            passed=passed,
        ),
        clash_results=(
            ClashResult(
                element_a_guid="guid-a",
                element_b_guid="guid-b",
                clash_type="hard",
                distance=0.015,
                description="Hard clash between wall and pipe",
            ),
        ),
    )


class FilesystemAuditStoreTests(unittest.TestCase):
    def test_save_and_get_roundtrip(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemAuditStore(Path(tmp))
            report = _make_report("rpt-roundtrip", passed=True)

            stored_id = store.save(report)
            self.assertEqual(stored_id, "rpt-roundtrip")

            loaded = store.get("rpt-roundtrip")
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded.report_id, "rpt-roundtrip")
            self.assertEqual(loaded.request_id, "req-001")
            self.assertEqual(loaded.created_at, "2026-04-09T12:00:00Z")
            self.assertTrue(loaded.summary.passed)

    def test_get_nonexistent_returns_none(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemAuditStore(Path(tmp))
            self.assertIsNone(store.get("does-not-exist"))

    def test_list_reports_returns_summaries(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemAuditStore(Path(tmp))
            store.save(_make_report("rpt-a", passed=True, issue_count=0))
            store.save(_make_report("rpt-b", passed=False, issue_count=3))

            entries = store.list_reports()
            self.assertEqual(len(entries), 2)
            ids = {e.report_id for e in entries}
            self.assertEqual(ids, {"rpt-a", "rpt-b"})

            failed_entry = next(e for e in entries if e.report_id == "rpt-b")
            self.assertFalse(failed_entry.passed)
            self.assertEqual(failed_entry.issue_count, 3)

    def test_atomic_write_produces_json_file(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemAuditStore(Path(tmp))
            store.save(_make_report("rpt-json"))

            json_path = Path(tmp) / "reports" / "rpt-json.json"
            self.assertTrue(json_path.exists())

            data = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(data["report_id"], "rpt-json")

    def test_no_tmp_files_remain_after_save(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemAuditStore(Path(tmp))
            store.save(_make_report("rpt-clean"))

            tmp_files = list((Path(tmp) / "reports").glob("*.tmp"))
            self.assertEqual(len(tmp_files), 0)

    def test_save_and_get_preserve_clash_results(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemAuditStore(Path(tmp))
            store.save(_make_report("rpt-clash"))

            loaded = store.get("rpt-clash")
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(len(loaded.clash_results), 1)
            self.assertEqual(loaded.clash_results[0].element_a_guid, "guid-a")
            self.assertEqual(loaded.clash_results[0].element_b_guid, "guid-b")
            self.assertEqual(loaded.clash_results[0].clash_type, "hard")
            self.assertAlmostEqual(loaded.clash_results[0].distance, 0.015)


if __name__ == "__main__":
    unittest.main()
