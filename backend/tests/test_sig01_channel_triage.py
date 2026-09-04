
"""SIG-01 channel Red Team triage stays NO_GO and encodes KILL brakes."""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.finding_volume import REPORT_PHRASE, VOLUME_CLASS_UNRESTRICTED_EQ_SAMPLE
from aerobim.domain.sig01_channel_triage import TRIAGE_ROWS, triage_snapshot
from aerobim.domain.target_ref import UNRESTRICTED_ELEMENT_MISMATCH_CAP


class Sig01ChannelTriageTests(unittest.TestCase):
    def test_snapshot_stays_no_go(self) -> None:
        snap = triage_snapshot()
        self.assertEqual(snap["checkpoint"], CHECKPOINT)
        self.assertEqual(snap["detected_count"], 0)
        self.assertFalse(snap["closes_rt001"])
        self.assertFalse(snap["closes_rt002"])
        self.assertFalse(snap["closes_rt003"])
        self.assertFalse(snap["is_accuracy"])
        self.assertFalse(snap["is_pack_processed"])
        self.assertFalse(snap["is_customer_defect_list"])
        self.assertFalse(snap["channel_totals_in_git"])
        self.assertEqual(snap["publishable_finding_count"], 0)
        self.assertEqual(snap["report_phrase"], REPORT_PHRASE)
        self.assertEqual(snap["unrestricted_eq_sample_class"], VOLUME_CLASS_UNRESTRICTED_EQ_SAMPLE)
        self.assertEqual(snap["mismatch_cap"], UNRESTRICTED_ELEMENT_MISMATCH_CAP)
        self.assertGreaterEqual(snap["unsigned_overlap_group_count"], 6)
        self.assertEqual(
            snap["kill_count"] + snap["hold_count"] + snap["accept_count"],
            len(TRIAGE_ROWS),
        )
        self.assertGreaterEqual(snap["kill_count"], 18)
        self.assertGreaterEqual(snap["accept_count"], 3)

    def test_ids_unique_and_verdicts_known(self) -> None:
        ids = [row["id"] for row in TRIAGE_ROWS]
        self.assertEqual(len(ids), len(set(ids)))
        allowed = {"KILL", "HOLD", "ACCEPT"}
        for row in TRIAGE_ROWS:
            self.assertIn(row["verdict"], allowed)
            self.assertTrue(row["brake"])

    def test_markdown_lists_every_triage_id(self) -> None:
        md = (
            Path(__file__).resolve().parents[2]
            / "docs"
            / "quality"
            / "SIG01_CHANNEL_TRIAGE_2026_08.md"
        ).read_text(encoding="utf-8")
        for row in TRIAGE_ROWS:
            self.assertIn(f"| {row['id']} |", md, msg=row["id"])
        self.assertIn(REPORT_PHRASE, md)
        self.assertIn("customer_go", md)
        self.assertNotIn("pack_hash", md)

    def test_required_kill_ids(self) -> None:
        ids = {row["id"] for row in TRIAGE_ROWS}
        for row_id in (
            "RT-SIG01-ACCURACY",
            "RT-SIG01-DEFECT",
            "RT-SIG01-PACK",
            "RT-SIG01-SP",
            "RT-SIG01-EI45",
            "RT-SIG01-CAP-RAISE",
            "RT-SIG01-SUPPRESS-N",
            "RT-SIG01-EQ-AS-DETECT",
            "RT-SIG01-OVERLAP",
            "RT-SIG01-KR-DOOR",
            "RT-SIG01-PDF-HITL",
            "RT-SIG01-PDF-GIT",
            "RT-SIG01-QTO-TEP",
            "RT-SIG01-SLA",
            "RT-SIG01-MEP",
            "RT-SIG01-IDS",
            "RT-SIG01-F1",
            "RT-SIG01-RAIL",
            "RT-SIG01-ALL-FIX",
            "RT-SIG01-GUID-FIX",
            "RT-SIG01-EXISTS-FIX",
        ):
            self.assertIn(row_id, ids)


if __name__ == "__main__":
    unittest.main()
