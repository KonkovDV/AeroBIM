"""HITL share on the synthetic drawing-advisory fixture rises with the floor."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.abstention_sweep import SWEEP_TAUS, sweep_region_cases


def _cases() -> list[dict[str, object]]:
    path = (
        Path(__file__).resolve().parents[2]
        / "samples"
        / "benchmarks"
        / "drawing-advisory"
        / "cases-synthetic.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload["cases"]
    assert isinstance(cases, list)
    return cases


class AbstentionSweepTests(unittest.TestCase):
    def test_hitl_rate_does_not_fall_as_the_floor_rises(self) -> None:
        recorded = sweep_region_cases(_cases(), SWEEP_TAUS)
        counterfactual = sweep_region_cases(
            _cases(),
            SWEEP_TAUS,
            calibrated_counterfactual=True,
        )
        self.assertFalse(recorded["publishable"])
        self.assertEqual(recorded["claim_level"], "fixture_only")
        self.assertIsNone(recorded["brier"])
        self.assertIsNone(recorded["ece"])
        self.assertTrue(recorded["hitl_rate_nondecreasing"])
        self.assertTrue(counterfactual["hitl_rate_nondecreasing"])
        recorded_points = recorded["points"]
        counter_points = counterfactual["points"]
        assert isinstance(recorded_points, list)
        assert isinstance(counter_points, list)
        self.assertEqual([point["tau"] for point in recorded_points], list(SWEEP_TAUS))
        self.assertGreater(counter_points[-1]["hitl_rate"], counter_points[0]["hitl_rate"])

    def test_thresholds_must_be_ordered(self) -> None:
        with self.assertRaises(ValueError):
            sweep_region_cases(_cases(), (0.75, 0.35))
