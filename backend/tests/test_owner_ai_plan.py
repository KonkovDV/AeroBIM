"""Owner-AI plan stays NO_GO; owner-blocked items are explicit."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.owner_ai_plan import (
    DESIGN_TZ_EXTRACTOR_HITS,
    DESIGN_TZ_EXTRACTOR_STATUS,
    PLAN_ITEMS,
    plan_snapshot,
)
from aerobim.domain.tz_v1_brief import PAPER_OBJECTS

_REPO = Path(__file__).resolve().parents[2]
_EVIDENCE = _REPO / "docs" / "evidence" / "owner-ai-plan-execution-2026-08.json"


class OwnerAiPlanTests(unittest.TestCase):
    def test_snapshot_stays_no_go(self) -> None:
        snap = plan_snapshot()
        self.assertEqual(snap["checkpoint"], CHECKPOINT)
        self.assertEqual(snap["detected_count"], 0)
        self.assertFalse(snap["closes_rt001"])
        self.assertFalse(snap["closes_rt002"])
        self.assertFalse(snap["closes_rt003"])
        self.assertFalse(snap["raise_ifc_cap"])
        self.assertFalse(snap["parse_rvt_nwd_lira"])
        self.assertFalse(snap["precision_claim_publishable"])
        self.assertEqual(snap["seven_task_criterion"], "Uncertain")
        self.assertEqual(snap["mik_m2_m8"], "VERIFY_WITH_OPERATOR")
        self.assertEqual(tuple(snap["paper_objects"]), PAPER_OBJECTS)
        self.assertFalse(snap["mik_act_may_cite_tz_v1_accuracy_as_measured"])

    def test_extraction_gap_is_not_absent_requirements(self) -> None:
        gap = plan_snapshot()["extraction_gap"]
        self.assertEqual(gap["status"], DESIGN_TZ_EXTRACTOR_STATUS)
        self.assertEqual(gap["deterministic_hits"], DESIGN_TZ_EXTRACTOR_HITS)
        self.assertIn("REI60", gap["licensed"])
        self.assertIn("no fire", gap["blocked"].casefold())

    def test_oos_templates_unsigned(self) -> None:
        oos = plan_snapshot()["oos"]
        self.assertFalse(oos["any_accepted"])
        self.assertTrue(oos["templates_unsigned"])

    def test_ids_unique_and_owner_blocked_present(self) -> None:
        ids = [row["id"] for row in PLAN_ITEMS]
        self.assertEqual(len(ids), len(set(ids)))
        snap = plan_snapshot()
        self.assertGreaterEqual(snap["owner_blocked_count"], 5)
        self.assertGreaterEqual(snap["agent_done_count"], 6)
        self.assertEqual(snap["item_count"], len(PLAN_ITEMS))

    def test_inventory_pin_has_no_pack_hash(self) -> None:
        inv = plan_snapshot()["inventory"]
        self.assertFalse(inv["names_in_git"])
        self.assertFalse(inv["hashes_in_git"])
        self.assertNotIn("pack_hash", inv)

    def test_evidence_json_matches_snapshot(self) -> None:
        dumped = json.loads(_EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(dumped, plan_snapshot())


if __name__ == "__main__":
    unittest.main()
