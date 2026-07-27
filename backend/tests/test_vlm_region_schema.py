"""§4 rich observation schema — grounding + deterministic normalizer tests.

Contract: bbox_rel out-of-range/degenerate or bad kind → drop the observation
(not the whole answer); confidence clamped + abstention→HITL; normalized_value
is OUR deterministic value (the model's is ignored); structural deviation →
fail-closed.
"""

from __future__ import annotations

import unittest

from aerobim.domain.vlm_grounding import ground_vlm_region_observations
from aerobim.domain.vlm_normalize import is_allowed_kind, normalize_observation_value


class NormalizerTests(unittest.TestCase):
    def test_designation_drops_ws_and_uppercases(self) -> None:
        self.assertEqual(normalize_observation_value("designation", "ст 1"), "СТ1")
        self.assertEqual(normalize_observation_value("designation", " d-2 "), "D-2")

    def test_dimension_comma_to_dot_no_spaces(self) -> None:
        self.assertEqual(normalize_observation_value("dimension", "1 200,5"), "1200.5")

    def test_text_collapses_whitespace(self) -> None:
        self.assertEqual(normalize_observation_value("text", "a\n  b\t c"), "a b c")

    def test_empty_is_none(self) -> None:
        self.assertIsNone(normalize_observation_value("text", "   "))

    def test_allowed_kinds(self) -> None:
        self.assertTrue(is_allowed_kind("STAMP_FIELD"))
        self.assertFalse(is_allowed_kind("counting"))


def _obs(bbox, *, kind="designation", raw="Ст-1", conf=0.9, extra=None):  # noqa: ANN001
    o = {"kind": kind, "raw_value": raw, "bbox_rel": bbox, "confidence": conf}
    if extra:
        o.update(extra)
    return o


class RegionObservationGroundingTests(unittest.TestCase):
    def test_valid_observations_grounded_with_our_normalization(self) -> None:
        raw = {
            "readable": True,
            "observations": [
                _obs([0.1, 0.1, 0.4, 0.3], raw="ст 1"),
                _obs([0.0, 0.0, 0.5, 0.5], kind="dimension", raw="2 400,0", conf=0.5),
            ],
        }
        res = ground_vlm_region_observations(raw, sheet_id="AR-01", region_id="stamp")
        self.assertTrue(res.parse_ok)
        self.assertEqual(len(res.observations), 2)
        self.assertEqual(res.observations[0].normalized_value, "СТ1")
        self.assertEqual(res.observations[1].normalized_value, "2400.0")
        self.assertEqual(res.hitl_count, 1)  # 0.5 < 0.6 → abstain
        self.assertTrue(res.observations[1].hitl_required)

    def test_model_normalized_value_is_ignored(self) -> None:
        raw = {
            "observations": [
                _obs([0.1, 0.1, 0.4, 0.3], raw="ст 1", extra={"normalized_value": "WRONG"})
            ]
        }
        res = ground_vlm_region_observations(raw, sheet_id="S1", region_id="r1")
        self.assertEqual(res.observations[0].normalized_value, "СТ1")

    def test_degenerate_or_out_of_range_bbox_dropped_not_whole(self) -> None:
        raw = {
            "observations": [
                _obs([0.1, 0.1, 0.1, 0.3]),  # x1==x2 degenerate → drop
                _obs([0.0, 0.0, 1.5, 0.5]),  # x2>1 out of range → drop
                _obs([0.2, 0.2, 0.4, 0.4]),  # valid
            ]
        }
        res = ground_vlm_region_observations(raw, sheet_id="S1", region_id="r1")
        self.assertTrue(res.parse_ok)  # whole answer survives
        self.assertEqual(len(res.observations), 1)
        self.assertEqual(res.dropped_count, 2)
        self.assertIn("dropped", res.reason or "")

    def test_bad_kind_dropped(self) -> None:
        raw = {"observations": [_obs([0.1, 0.1, 0.4, 0.3], kind="counting")]}
        res = ground_vlm_region_observations(raw, sheet_id="S1", region_id="r1")
        self.assertTrue(res.parse_ok)
        self.assertEqual(res.observations, ())
        self.assertEqual(res.dropped_count, 1)

    def test_nan_confidence_clamped_and_abstains(self) -> None:
        raw = {"observations": [_obs([0.1, 0.1, 0.4, 0.3], conf=float("nan"))]}
        res = ground_vlm_region_observations(raw, sheet_id="S1", region_id="r1")
        self.assertEqual(res.observations[0].confidence, 0.0)
        self.assertTrue(res.observations[0].hitl_required)

    def test_structural_deviation_fails_closed(self) -> None:
        for bad in ("not-an-object", {"no_observations": True}, {"observations": "x"}):
            res = ground_vlm_region_observations(bad, sheet_id="S1", region_id="r1")
            self.assertFalse(res.parse_ok, bad)
            self.assertEqual(res.observations, ())

    def test_unreadable_region_reports_reason(self) -> None:
        raw = {"readable": False, "unreadable_reason": "blurred scan", "observations": []}
        res = ground_vlm_region_observations(raw, sheet_id="S1", region_id="r1")
        self.assertTrue(res.parse_ok)
        self.assertFalse(res.readable)
        self.assertEqual(res.reason, "blurred scan")


if __name__ == "__main__":
    unittest.main()
