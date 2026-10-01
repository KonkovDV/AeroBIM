"""Tracker six tasks stay NO_GO and do not invent demo counts."""

from __future__ import annotations

import unittest

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.tracker_six_tasks import TRACKER_TASKS, tracker_snapshot


class TrackerSixTasksTests(unittest.TestCase):
    def test_snapshot_stays_no_go(self) -> None:
        snap = tracker_snapshot()
        self.assertEqual(snap["checkpoint"], CHECKPOINT)
        self.assertEqual(snap["detected_count"], 0)
        self.assertFalse(snap["closes_rt001"])
        self.assertFalse(snap["scheduled_demos_in_git"])
        self.assertEqual(snap["item_count"], 6)
        self.assertEqual(len(TRACKER_TASKS), 6)
        ids = [row["id"] for row in TRACKER_TASKS]
        self.assertEqual(ids, [f"TRK-0{i}" for i in range(1, 7)])
        self.assertGreaterEqual(snap["owner_blocked_count"], 4)
        self.assertIn("Tangl", snap["speech_tangl"])
        self.assertIn("run_kt3_jury", TRACKER_TASKS[0]["kt3_show"])


if __name__ == "__main__":
    unittest.main()
