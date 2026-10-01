"""SPG speech Red Team triage stays NO_GO; consulting pin stays off jury hop."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.jury_pack_triage import JURY_SURFACES
from aerobim.domain.spg_speech_triage import TRIAGE_ROWS, spg_speech_triage_snapshot


class SpgSpeechTriageTests(unittest.TestCase):
    def _repo(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def test_snapshot_stays_no_go(self) -> None:
        snap = spg_speech_triage_snapshot()
        self.assertEqual(snap["checkpoint"], CHECKPOINT)
        self.assertEqual(snap["detected_count"], 0)
        self.assertFalse(snap["is_sam"])
        self.assertFalse(snap["is_fm_product"])
        self.assertFalse(snap["pdf_in_git"])
        self.assertFalse(snap["on_tier0"])
        self.assertEqual(snap["artifact_type"], "spg_speech_red_team_triage")
        self.assertEqual(
            snap["kill_count"] + snap["hold_count"] + snap["accept_count"],
            len(TRIAGE_ROWS),
        )
        self.assertGreaterEqual(snap["kill_count"], 11)
        blob = json.dumps(snap)
        self.assertNotIn("ГиБ", blob)
        self.assertNotIn("GiB", blob)

    def test_ids_unique_and_markdown_lists_them(self) -> None:
        ids = [row["id"] for row in TRIAGE_ROWS]
        self.assertEqual(len(ids), len(set(ids)))
        md = (self._repo() / "docs" / "quality" / "SPG_CONSTRUCTION_VS_FM_2026_09.md").read_text(
            encoding="utf-8"
        )
        for row in TRIAGE_ROWS:
            self.assertIn(f"| {row['id']} |", md, msg=row["id"])
        self.assertIn("customer_go", md)

    def test_jury_surfaces_omit_consulting_pin_filename(self) -> None:
        repo = self._repo()
        token = "SPG_CONSTRUCTION_VS_FM"
        for rel in JURY_SURFACES:
            text = (repo / rel).read_text(encoding="utf-8")
            self.assertNotIn(token, text, msg=rel)
        tier0 = (repo / "docs" / "TIER0_INDEX.md").read_text(encoding="utf-8")
        self.assertNotIn(token, tier0)


if __name__ == "__main__":
    unittest.main()
