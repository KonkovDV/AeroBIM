"""Tracker eight tasks (29.08) stay NO_GO and do not invent accuracy."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.finding_volume import volume_from_findings
from aerobim.domain.tracker_eight_tasks import TRACKER_EIGHT, tracker_eight_snapshot
from aerobim.tools.run_finding_volume import main as finding_volume_main


class TrackerEightTasksTests(unittest.TestCase):
    def test_snapshot_stays_no_go_and_locks_gigachat_errors(self) -> None:
        snap = tracker_eight_snapshot()
        self.assertEqual(snap["checkpoint"], "NO_GO")
        self.assertEqual(snap["item_count"], 8)
        self.assertEqual(len(TRACKER_EIGHT), 8)
        self.assertEqual([row["id"] for row in TRACKER_EIGHT], [f"SIG-0{i}" for i in range(1, 9)])
        self.assertGreaterEqual(snap["owner_blocked_count"], 7)
        self.assertFalse(snap["raises_spf_default_for_ingest"])
        self.assertEqual(snap["spf_analyze_cap_bytes"], 256 * 1024 * 1024)
        self.assertEqual(snap["ingest_cap_bytes"], 1_500_000_000)
        self.assertEqual(snap["cadsofttools_usd_retrieved"], 765)
        self.assertTrue(snap["cadsofttools_stale_list_price"])
        self.assertEqual(snap["rt002a"], "CLOSED")
        self.assertEqual(snap["rt002b"], "OPEN")
        self.assertEqual(snap["auth_bff_status"], "NOT_IMPLEMENTED")
        self.assertFalse(snap["finding_volume_is_accuracy"])
        self.assertEqual(snap["sig01_report_phrase"], "объём находок на канале получен")
        self.assertEqual(snap["sig01_publishable_finding_count"], 0)
        self.assertEqual(snap["channel_max_pass"], "channel_local_max_pass_snapshot")
        self.assertEqual(snap["pack_family_facts"], "pack_family_snapshot")
        self.assertFalse(snap["customer_pack_in_git"])
        self.assertEqual(snap["samolet_appendix4_task"], 6)
        self.assertEqual(snap["commission_order_number"], 7)
        self.assertEqual(snap["space_efficiency_kt3"], "advisory_unsigned")
        self.assertFalse(snap["space_efficiency_delivered"])
        self.assertEqual(snap["feature_freeze"], "2026-09-18")
        blob = json.dumps(snap)
        self.assertNotIn("1660", blob)
        self.assertNotIn("sgnl", blob.lower())
        self.assertNotIn("Siginevich", blob)
        self.assertNotIn("Dmitry", blob)

    def test_catalog_has_at_least_twenty_unconfirmed_classes(self) -> None:
        path = (
            Path(__file__).resolve().parents[2]
            / "samples"
            / "benchmarks"
            / "samolet-typical-errors-catalog.json"
        )
        catalog = json.loads(path.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(catalog["patterns"]), 20)
        self.assertEqual(catalog["customer_confirmed_patterns"], 0)
        self.assertFalse(catalog["customer_share_ingested"])


class FindingVolumeTests(unittest.TestCase):
    def test_volume_is_not_accuracy(self) -> None:
        table = volume_from_findings(
            [
                {"category": "IDS_VALIDATION", "severity": "error"},
                {"category": "IDS_VALIDATION", "severity": "warning"},
                {"rule_id": "REQ-AREA-001", "severity": "error"},
            ]
        )
        self.assertEqual(table["total"], 3)
        self.assertFalse(table["is_accuracy"])
        self.assertEqual(table["by_type"]["IDS_VALIDATION"], 2)
        self.assertEqual(table["checkpoint"], "NO_GO")
        self.assertIn("Not product accuracy", table["claim_boundary"])
        self.assertEqual(table["report_phrase"], "объём находок на канале получен")
        self.assertFalse(table["is_pack_processed"])
        self.assertFalse(table["is_customer_defect_list"])

    def test_cli_refuses_output_inside_docs(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            gate = Path(tmp) / "gate.json"
            gate.write_text(
                json.dumps({"findings": [{"category": "IDS_VALIDATION", "severity": "error"}]}),
                encoding="utf-8",
            )
            self.assertEqual(
                finding_volume_main(
                    [
                        "--gate-json",
                        str(gate),
                        "--output",
                        str(repo / "docs" / "evidence" / "finding-volume.json"),
                    ]
                ),
                2,
            )


if __name__ == "__main__":
    unittest.main()
