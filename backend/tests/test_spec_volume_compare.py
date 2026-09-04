"""TR-67 spec-volume triple compare — logical collisions, not estimate QTO."""

from __future__ import annotations

import unittest

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.samolet_mvp_answers import samolet_mvp_answers_payload
from aerobim.domain.spec_volume_compare import (
    SpecVolumeLine,
    compare_spec_volumes,
    spec_volume_honesty_snapshot,
)


class SpecVolumeCompareTests(unittest.TestCase):
    def test_three_way_match_is_not_estimate_qto(self) -> None:
        lines = (
            SpecVolumeLine("W-1", spec_qty="10,0", schedule_qty="10.0", model_qty="10", unit="m3"),
        )
        result = compare_spec_volumes(lines)
        self.assertTrue(result.all_match)
        self.assertEqual(result.lines[0].outcome, "MATCH")
        self.assertIsNone(result.lines[0].finding_kind)
        self.assertFalse(result.closes_rt001)
        self.assertEqual(result.checkpoint, CHECKPOINT)

    def test_three_way_mismatch_is_logical_collision_not_match(self) -> None:
        lines = (
            SpecVolumeLine("W-1", spec_qty="10", schedule_qty="10", model_qty="12", unit="m3"),
        )
        result = compare_spec_volumes(lines)
        self.assertFalse(result.all_match)
        self.assertEqual(result.lines[0].outcome, "MISMATCH")
        self.assertEqual(result.lines[0].finding_kind, "logical_collision")
        self.assertFalse(result.closes_rt001)
        self.assertEqual(result.checkpoint, CHECKPOINT)

    def test_missing_model_qty_is_fail_closed(self) -> None:
        lines = (
            SpecVolumeLine("W-1", spec_qty="10", schedule_qty="10", model_qty=None, unit="m3"),
        )
        result = compare_spec_volumes(lines)
        self.assertFalse(result.all_match)
        self.assertEqual(result.lines[0].outcome, "SOURCE_MISSING")

    def test_honesty_snapshot_rejects_estimate_qto_and_customer_pack(self) -> None:
        snap = spec_volume_honesty_snapshot()
        self.assertEqual(snap["checkpoint"], CHECKPOINT)
        self.assertFalse(snap["closes_rt001"])
        self.assertEqual(snap["estimate_qto"], "not_in_scope")
        self.assertEqual(snap["customer_pack"], "not_ingested")
        boundary = str(snap["claim_boundary"]).lower()
        self.assertIn("not", boundary)
        self.assertNotIn("smeta", boundary)
        payload = samolet_mvp_answers_payload()
        self.assertEqual(payload["spec_volume_compare"], snap)


if __name__ == "__main__":
    unittest.main()
