"""Live-tree Red Team triage stays NO_GO and encodes KILL brakes."""

from __future__ import annotations

import unittest

from aerobim.domain.live_tree_triage import TRIAGE_ROWS, triage_snapshot
from aerobim.domain.tz_v1_brief import (
    PAPER_OBJECTS,
    mik_act_may_cite_tz_v1_accuracy_as_measured,
    v1_brief_snapshot,
)


class LiveTreeTriageTests(unittest.TestCase):
    def test_snapshot_stays_no_go(self) -> None:
        snap = triage_snapshot()
        self.assertEqual(snap["checkpoint"], "NO_GO")
        self.assertEqual(snap["detected_count"], 0)
        self.assertFalse(snap["closes_rt001"])
        self.assertFalse(snap["closes_rt002"])
        self.assertFalse(snap["closes_rt003"])
        self.assertEqual(
            snap["kill_count"] + snap["hold_count"] + snap["accept_count"],
            len(TRIAGE_ROWS),
        )
        self.assertGreaterEqual(snap["kill_count"], 6)

    def test_ids_unique_and_verdicts_known(self) -> None:
        ids = [row["id"] for row in TRIAGE_ROWS]
        self.assertEqual(len(ids), len(set(ids)))
        allowed = {"KILL", "HOLD", "ACCEPT"}
        for row in TRIAGE_ROWS:
            self.assertIn(row["verdict"], allowed)
            self.assertTrue(row["brake"])

    def test_v1_kill_brakes_are_wired(self) -> None:
        self.assertFalse(mik_act_may_cite_tz_v1_accuracy_as_measured())
        snap = v1_brief_snapshot()
        self.assertEqual(len(snap["paper_objects"]), 4)
        self.assertEqual(tuple(snap["paper_objects"]), PAPER_OBJECTS)
        self.assertFalse(snap["pdf"]["binary_in_git"])
        self.assertNotIn("pack_hash", snap)
        self.assertNotIn("customer_pack_hash", snap)
        self.assertEqual(snap["evaluation"]["pilot_interim_precision"], 0.60)


if __name__ == "__main__":
    unittest.main()
