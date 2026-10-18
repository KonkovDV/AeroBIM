"""Null ensemble: e-process crossings stay inside Ville's band; naive alpha does not."""

from __future__ import annotations

import unittest

from aerobim.domain.e_process_simulation import simulate_null_trajectories


class EProcessSimulationTests(unittest.TestCase):
    def test_crossing_rates_respect_the_ville_band(self) -> None:
        report = simulate_null_trajectories()
        self.assertFalse(report["publishable"])
        self.assertEqual(report["corpus_kind"], "synthetic_null")
        bound = report["crossing_rate_bound"]
        assert isinstance(bound, float)
        for key in (
            "mixture_crossing_rate",
            "power_crossing_rate",
            "betting_crossing_rate",
        ):
            rate = report[key]
            assert isinstance(rate, float)
            self.assertLessEqual(rate, bound, msg=key)
        naive = report["naive_alarm_rate"]
        assert isinstance(naive, float)
        self.assertGreater(naive, report["alpha"])
        self.assertGreater(naive, report["mixture_crossing_rate"])
