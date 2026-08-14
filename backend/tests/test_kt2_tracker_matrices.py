from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.tools.export_ifc_release_matrix import build_ifc_release_matrix
from aerobim.tools.run_vlm_stamp_comparison import build_vlm_comparison


class IfcReleaseMatrixShapeTests(unittest.TestCase):
    def test_builds_fixture_only_rows_from_committed_suite(self) -> None:
        root = Path(__file__).resolve().parents[2]
        suite_path = root / "audit" / "evidence" / "ifc-release-benchmark-2026-08.json"
        if not suite_path.is_file():
            self.skipTest("committed IFC suite evidence missing")
        suite = json.loads(suite_path.read_text(encoding="utf-8"))
        matrix = build_ifc_release_matrix(suite)
        self.assertEqual(matrix["claim_level"], "fixture_only")
        self.assertTrue(matrix["customer_accuracy_not_established"])
        schemas = {row["schema"] for row in matrix["rows"]}
        self.assertEqual(schemas, {"IFC2X3", "IFC4", "IFC4X3"})
        for row in matrix["rows"]:
            self.assertIsNotNone(row["ifc_entity_count"])
            self.assertIn("Pset", row["pset_name_mismatch_policy"])
        self.assertIn("content_sha256", matrix)


class VlmStampComparisonSkipTests(unittest.TestCase):
    def test_without_key_is_skipped_with_no_metrics(self) -> None:
        payload = build_vlm_comparison(api_key_present=False)
        self.assertEqual(payload["status"], "SKIPPED")
        self.assertIsNone(payload["metrics"])
        self.assertEqual(payload["claim_level"], "fixture_only")
        self.assertIn("stamp", payload["scenario"])
        self.assertIn("door_count", payload["not_in_scope"])
        self.assertEqual(payload["comparison_status"], "comparison_not_run")
        self.assertEqual(payload["kimi_status"], "GATED")
        self.assertEqual(payload["qwen_fixture_status"], "not_run_in_this_payload")


if __name__ == "__main__":
    unittest.main()
