from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    ReportCapabilities,
    Severity,
    ValidationIssue,
)
from aerobim.tools.export_ifc_release_matrix import (
    build_ifc_release_matrix,
    digest_rules_and_refusals,
)
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

    def test_digest_lists_fired_rules_and_honesty_refusals(self) -> None:
        issues = (
            ValidationIssue(
                rule_id="AEROBIM-IDS-IFC-VERSION", severity=Severity.ERROR, message="x"
            ),
            ValidationIssue(
                rule_id="AEROBIM-IDS-IFC-VERSION", severity=Severity.ERROR, message="y"
            ),
            ValidationIssue(rule_id="AEROBIM-QTO-MISSING", severity=Severity.WARNING, message="z"),
        )
        caps = ReportCapabilities(
            ids=CapabilityStatus(CapabilityState.OK, "ids ran"),
            dwg_dxf=CapabilityStatus(
                CapabilityState.MISSING, "native DWG parser is not implemented"
            ),
            clash=CapabilityStatus(CapabilityState.SKIPPED, "clash detection not evaluated"),
        )
        digest = digest_rules_and_refusals(issues, caps)
        self.assertEqual(digest["rules_fired"]["AEROBIM-IDS-IFC-VERSION"], 2)
        self.assertEqual(digest["severity_counts"]["error"], 2)
        names = {item["capability"] for item in digest["refusals"]}
        self.assertIn("dwg_dxf", names)
        self.assertIn("clash", names)
        self.assertIn("ids", digest["capabilities_ok"])


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
