"""Jury-pack Red Team triage stays NO_GO; unpack fingerprints stay off jury surfaces."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.jury_pack_triage import (
    JURY_FINGERPRINT_TOKENS,
    JURY_SURFACES,
    TRIAGE_ROWS,
    jury_pack_triage_snapshot,
)


class JuryPackTriageTests(unittest.TestCase):
    def _repo(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def test_snapshot_stays_no_go(self) -> None:
        snap = jury_pack_triage_snapshot()
        self.assertEqual(snap["checkpoint"], CHECKPOINT)
        self.assertEqual(snap["detected_count"], 0)
        self.assertFalse(snap["closes_rt001"])
        self.assertFalse(snap["is_pack_processed"])
        self.assertFalse(snap["names_in_git"])
        self.assertFalse(snap["sitting_member_list_in_git"])
        self.assertEqual(snap["seven_task_criterion"], "Uncertain")
        self.assertEqual(snap["artifact_type"], "jury_pack_red_team_triage")
        self.assertNotIn("family", snap)
        self.assertEqual(
            snap["kill_count"] + snap["hold_count"] + snap["accept_count"],
            len(TRIAGE_ROWS),
        )
        self.assertGreaterEqual(snap["kill_count"], 17)
        self.assertGreaterEqual(snap["hold_count"], 2)
        self.assertGreaterEqual(snap["accept_count"], 5)
        blob = json.dumps(snap)
        self.assertNotIn("ГиБ", blob)
        self.assertNotIn("GiB", blob)
        self.assertNotIn("pack_hash", blob)
        self.assertNotIn("sha256", blob)

    def test_ids_unique_and_verdicts_known(self) -> None:
        ids = [row["id"] for row in TRIAGE_ROWS]
        self.assertEqual(len(ids), len(set(ids)))
        allowed = {"KILL", "HOLD", "ACCEPT"}
        for row in TRIAGE_ROWS:
            self.assertIn(row["verdict"], allowed)
            self.assertTrue(row["brake"])

    def test_required_ids(self) -> None:
        ids = {row["id"] for row in TRIAGE_ROWS}
        for row_id in (
            "RT-JURY-FIO",
            "RT-JURY-HOMONYM",
            "RT-JURY-TRACKER-NAME",
            "RT-JURY-TIER0-CENSUS",
            "RT-JURY-TIER0-SHORTLIST",
            "RT-JURY-PROCESSED",
            "RT-JURY-TANGL",
            "RT-JURY-GIGACHAT",
            "RT-JURY-CHANNEL-BRAND",
            "RT-JURY-OSINT-GIT",
            "RT-JURY-LOCAL-PIN",
            "RT-JURY-GIB",
            "RT-JURY-QUESTION-EXHIBIT",
            "RT-JURY-OA-EXHIBIT",
            "RT-JURY-MEETS",
            "RT-JURY-ENG-PINS",
            "RT-JURY-DENYLIST",
            "RT-JURY-SEATS-ROLES",
            "RT-JURY-OSINT-IGNORED",
            "RT-JURY-RENAME",
            "RT-JURY-TIER0-SHRINK",
            "RT-JURY-NOT-EXHIBIT",
            "RT-JURY-SPG-HOP",
            "RT-JURY-UI-LIVE",
            "RT-JURY-TZ-UI-DONE",
        ):
            self.assertIn(row_id, ids)

    def test_markdown_lists_every_triage_id(self) -> None:
        md = (self._repo() / "docs" / "quality" / "JURY_PACK_TRIAGE_2026_09.md").read_text(
            encoding="utf-8"
        )
        for row in TRIAGE_ROWS:
            self.assertIn(f"| {row['id']} |", md, msg=row["id"])
        self.assertIn("customer_go", md)
        self.assertNotIn("pack_hash", md)
        self.assertNotIn("81 ГиБ", md)
        self.assertNotIn("61,15", md)

    def test_jury_surfaces_omit_unpack_fingerprints(self) -> None:
        repo = self._repo()
        for rel in JURY_SURFACES:
            text = (repo / rel).read_text(encoding="utf-8")
            for token in JURY_FINGERPRINT_TOKENS:
                self.assertNotIn(token, text, msg=f"{rel}: {token}")


if __name__ == "__main__":
    unittest.main()
