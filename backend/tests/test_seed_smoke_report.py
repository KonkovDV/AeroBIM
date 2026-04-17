from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.tools.seed_smoke_report import SMOKE_REPORT_ID, seed_smoke_report


class SeedSmokeReportTests(unittest.TestCase):
    def test_seed_smoke_report_materializes_runtime_review_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir)

            report = seed_smoke_report(storage_dir)

            self.assertEqual(report.report_id, SMOKE_REPORT_ID)
            self.assertTrue(report.ifc_path.exists())
            self.assertTrue(report.ifc_path.is_relative_to(storage_dir.resolve()))
            self.assertEqual(len(report.issues), 1)
            self.assertEqual(report.issues[0].rule_id, "SMOKE-DRAW-001")
            self.assertIsNotNone(report.issues[0].element_guid)
            self.assertIsNotNone(report.issues[0].problem_zone)
            self.assertEqual(len(report.clash_results), 1)
            self.assertEqual(len(report.drawing_assets), 2)
            preview_dir = storage_dir / "drawing-assets" / report.report_id
            self.assertTrue(preview_dir.exists())
            self.assertEqual(len(list(preview_dir.glob("*.png"))), 2)

    def test_seed_smoke_report_is_idempotent_for_same_storage_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir)

            first = seed_smoke_report(storage_dir)
            second = seed_smoke_report(storage_dir)

            self.assertEqual(first.report_id, second.report_id)
            preview_dir = storage_dir / "drawing-assets" / second.report_id
            self.assertEqual(len(list(preview_dir.glob("*.png"))), 2)
