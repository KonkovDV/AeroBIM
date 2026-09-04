
"""Public seven-task cartography stays coverage_map_only (not detection)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT

REPO_ROOT = Path(__file__).resolve().parents[2]
CARTOGRAPHY = REPO_ROOT / "docs" / "evidence" / "techlab-seven-tasks-cartography-2026-08.json"


class TechlabCartographyHonestyTests(unittest.TestCase):
    def test_git_twin_does_not_close_rt_or_claim_meets(self) -> None:
        payload = json.loads(CARTOGRAPHY.read_text(encoding="utf-8"))
        self.assertEqual(payload["claim_level"], "coverage_map_only")
        self.assertEqual(payload["checkpoint"], CHECKPOINT)
        self.assertEqual(payload["detected_count"], 0)
        self.assertFalse(payload["closes_rt001"])
        self.assertFalse(payload["closes_rt002"])
        self.assertFalse(payload["closes_rt003"])
        self.assertEqual(payload["n_cells"], 51)
        self.assertTrue(payload.get("redacted_for_git"))
        blob = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn("нет замечаний", blob)
        self.assertNotIn("65056", blob)
        for task in payload["tasks"]:
            self.assertEqual(task["four_state_for_criterion"], "Uncertain")


if __name__ == "__main__":
    unittest.main()
