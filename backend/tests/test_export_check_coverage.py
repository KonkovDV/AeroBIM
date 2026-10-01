"""P0 evidence: synthetic check-coverage map shows the full status vocabulary.

Проверяет, что демонстрационная карта покрытия (без данных заказчика, без сети)
показывает все статусы, строку (unattributed), verdict-neutral и воспроизводима
относительно зафиксированного артефакта.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.tools.export_check_coverage import synthetic_scenario

_ARTIFACT = (
    Path(__file__).resolve().parents[2] / "audit" / "evidence" / "check-coverage-2026-07-29.json"
)


class ExportCheckCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = synthetic_scenario()

    def test_full_status_vocabulary_present(self) -> None:
        summary = self.report["summary"]
        for status in (
            "checked_ok",
            "checked_findings",
            "not_checked",
            "insufficient_data",
            "requires_expert",
        ):
            self.assertGreater(summary[status], 0, status)

    def test_unattributed_row_present(self) -> None:
        source_ids = [row["source_id"] for row in self.report["sources"]]
        self.assertIn("(unattributed)", source_ids)

    def test_verdict_neutral(self) -> None:
        self.assertNotIn('"passed"', json.dumps(self.report))  # no verdict key anywhere
        self.assertNotIn("summary_passed", self.report)
        self.assertIn("verdict-neutral", self.report["note"])
        self.assertEqual(self.report["corpus"], "synthetic")

    def test_reproducible_vs_committed_artifact(self) -> None:
        self.assertTrue(_ARTIFACT.exists(), "check-coverage evidence artifact missing")
        # Regenerate on intentional change: python -m aerobim.tools.export_check_coverage
        committed = json.loads(_ARTIFACT.read_text(encoding="utf-8"))
        self.assertEqual(self.report, committed)


if __name__ == "__main__":
    unittest.main()
