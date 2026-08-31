"""Channel-pack Red Team triage stays NO_GO; GiB stays out of git."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.channel_pack_triage import TRIAGE_ROWS, pack_triage_snapshot
from aerobim.domain.pack_family_facts import LIRA_NAMED_EXT, pack_family_snapshot


class PackFamilyFactsTests(unittest.TestCase):
    def test_snapshot_stays_no_go_and_omits_gib(self) -> None:
        snap = pack_family_snapshot()
        self.assertEqual(snap["checkpoint"], "NO_GO")
        self.assertFalse(snap["processed"])
        self.assertFalse(snap["parse_lira"])
        self.assertFalse(snap["is_cc2_match"])
        self.assertFalse(snap["uncompressed_gib_in_git"])
        self.assertTrue(snap["calc_binaries_majority_of_unpack_bytes"])
        self.assertTrue(snap["live_walk_matched_evening_pin"])
        self.assertEqual(snap["unpack_file_count"], 6408)
        self.assertEqual(snap["tz_class_2_rd_files"], 0)
        self.assertEqual(snap["docx_with_class_phrase"], 6)
        self.assertEqual(snap["xlsx_with_load_token"], 46)
        self.assertTrue(snap["dxf_all_ascii"])
        self.assertIn(".lir", LIRA_NAMED_EXT)
        blob = json.dumps(snap)
        self.assertNotIn("pack_hash", blob)
        self.assertNotIn("sha256", blob)
        self.assertNotIn("ГиБ", blob)
        self.assertNotIn("GiB", blob)

    def test_evidence_json_matches_snapshot(self) -> None:
        dumped = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "docs"
                / "evidence"
                / "pack-family-facts-latest.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(dumped, pack_family_snapshot())


class ChannelPackTriageTests(unittest.TestCase):
    def test_snapshot_stays_no_go(self) -> None:
        snap = pack_triage_snapshot()
        self.assertEqual(snap["checkpoint"], "NO_GO")
        self.assertEqual(snap["detected_count"], 0)
        self.assertFalse(snap["closes_rt001"])
        self.assertFalse(snap["is_pack_processed"])
        self.assertFalse(snap["uncompressed_gib_in_git"])
        self.assertFalse(snap["is_cc2_match"])
        self.assertEqual(snap["seven_task_criterion"], "Uncertain")
        self.assertEqual(
            snap["kill_count"] + snap["hold_count"] + snap["accept_count"],
            len(TRIAGE_ROWS),
        )
        self.assertGreaterEqual(snap["kill_count"], 16)
        self.assertGreaterEqual(snap["hold_count"], 3)
        self.assertGreaterEqual(snap["accept_count"], 4)

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
            / "CHANNEL_PACK_TRIAGE_2026_08.md"
        ).read_text(encoding="utf-8")
        for row in TRIAGE_ROWS:
            self.assertIn(f"| {row['id']} |", md, msg=row["id"])
        self.assertIn("NO_GO", md)
        self.assertNotIn("pack_hash", md)
        self.assertNotIn("81 ГиБ", md)
        self.assertNotIn("61,15", md)

    def test_required_ids(self) -> None:
        ids = {row["id"] for row in TRIAGE_ROWS}
        for row_id in (
            "RT-PACK-PROCESSED",
            "RT-PACK-43GB",
            "RT-PACK-GIB",
            "RT-PACK-LIRA-SOLVE",
            "RT-PACK-TOKEN-MATCH",
            "RT-PACK-NAIVE-B",
            "RT-PACK-IFC-RERUN",
            "RT-PACK-STD-DEFECT",
            "RT-PACK-MAX-EVIDENCE",
            "RT-PACK-DXF-DWG",
            "RT-PACK-OCR",
            "RT-PACK-SCAN-FINDING",
            "RT-PACK-PP87",
            "RT-PACK-RD",
            "RT-PACK-MEETS",
            "RT-PACK-HASH-GIT",
            "RT-PACK-TXT-STUB",
            "RT-PACK-VOLUME-F1",
            "RT-PACK-OOXML-PARSE",
            "RT-PACK-OA9-SHARE",
            "RT-PACK-OCR-BUDGET",
            "RT-PACK-CENSUS-MATCH",
            "RT-PACK-HASH-LOCAL",
            "RT-PACK-CLASS-SHORTLIST",
            "RT-PACK-DXF-ASCII",
        ):
            self.assertIn(row_id, ids)


if __name__ == "__main__":
    unittest.main()
