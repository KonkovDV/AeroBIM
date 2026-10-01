"""Anytime-valid sequential regression monitoring (Wave O, Jul 2026).

Anchors: Vovk & Wang 2021 (Ann. Statist., p-to-e calibration); Ville 1939
(maximal inequality); Gruenwald, de Heide & Koolen 2024 (JRSS-B, safe
testing — irreversible rejection); Ramdas et al. 2023 (SAVI survey); arXiv
2501.03982 (anytime validity is free). Claim boundary: alarms concern the
fixture regression history only (RT-001).
"""

from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.eval_statistics import FixtureCounts, paired_permutation_test
from aerobim.domain.sequential_inference import (
    calibrate_p_to_e,
    calibrate_p_to_e_mixture,
    new_e_process_state,
    update_e_process,
)
from aerobim.tools.sequential_regression_monitor import main

_WORSE = FixtureCounts(true_positives=1, false_positives=1, false_negatives=0)  # F1=2/3
_BETTER = FixtureCounts(true_positives=1, false_positives=0, false_negatives=0)  # F1=1


class OneSidedPermutationTests(unittest.TestCase):
    def test_hand_enumerated_one_sided_less(self) -> None:
        """n=2, candidate uniformly worse: observed diff = -1/3. Masks:
        00 -> -1/3 (<= obs), 01/10 -> 0, 11 -> +1/3 => p_less = 1/4."""
        result = paired_permutation_test(
            [_BETTER, _BETTER], [_WORSE, _WORSE], metric="macro_f1", alternative="less"
        )
        self.assertTrue(result.exact)
        self.assertAlmostEqual(result.observed_diff, -1 / 3, places=12)
        self.assertEqual(result.p_value, 1 / 4)
        self.assertEqual(result.alternative, "less")

    def test_one_sided_greater_on_same_data_is_one(self) -> None:
        """All four masks give diff >= -1/3 => p_greater = 4/4 = 1."""
        result = paired_permutation_test(
            [_BETTER, _BETTER], [_WORSE, _WORSE], metric="macro_f1", alternative="greater"
        )
        self.assertEqual(result.p_value, 1.0)

    def test_uniform_regression_ten_pairs_less_p(self) -> None:
        """Only the identity mask reaches diff <= -1/3 => p = 1/1024."""
        result = paired_permutation_test(
            [_BETTER] * 10, [_WORSE] * 10, metric="macro_f1", alternative="less"
        )
        self.assertAlmostEqual(result.p_value, 1 / 1024, places=12)

    def test_two_sided_default_unchanged(self) -> None:
        result = paired_permutation_test([_WORSE] * 10, [_BETTER] * 10, metric="macro_f1")
        self.assertEqual(result.alternative, "two_sided")
        self.assertAlmostEqual(result.p_value, 2 / 1024, places=12)

    def test_unknown_alternative_rejected(self) -> None:
        with self.assertRaises(ValueError):
            paired_permutation_test([_WORSE], [_BETTER], alternative="bogus")


class CalibratorTests(unittest.TestCase):
    def test_power_calibrator_hand_values(self) -> None:
        """kappa=0.5: e = 0.5 / sqrt(p). p=0.04 -> 0.5/0.2 = 2.5 exactly;
        p=1 -> 0.5; p=0.25 -> 1.0."""
        self.assertAlmostEqual(calibrate_p_to_e(0.04), 2.5, places=12)
        self.assertAlmostEqual(calibrate_p_to_e(1.0), 0.5, places=12)
        self.assertAlmostEqual(calibrate_p_to_e(0.25), 1.0, places=12)

    def test_power_calibrator_mean_is_one_under_uniform(self) -> None:
        """E[kappa p^(kappa-1)] = 1 for p ~ U(0,1). The integrand is singular
        at 0, so the midpoint Riemann sum converges slowly from below —
        assert within 1e-2 (the sum at 2e5 steps is ~0.99932)."""
        steps = 200000
        total = sum(calibrate_p_to_e((i + 0.5) / steps, kappa=0.5) for i in range(steps))
        self.assertAlmostEqual(total / steps, 1.0, delta=0.01)

    def test_mixture_calibrator_hand_values(self) -> None:
        """F(1/e) = (1 - 2/e)·e = e - 2; F(e^-2) = (e^2 - 3)/4; F(1) = 1/2
        (second-order limit) — all derived by hand from the closed form."""
        self.assertAlmostEqual(calibrate_p_to_e_mixture(math.exp(-1)), math.e - 2, places=12)
        self.assertAlmostEqual(
            calibrate_p_to_e_mixture(math.exp(-2)), (math.e**2 - 3) / 4, places=12
        )
        self.assertAlmostEqual(calibrate_p_to_e_mixture(1.0), 0.5, places=9)

    def test_calibrators_reject_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            calibrate_p_to_e(0.5, kappa=1.0)
        with self.assertRaises(ValueError):
            calibrate_p_to_e(0.5, kappa=0.0)
        with self.assertRaises(ValueError):
            calibrate_p_to_e(1.5)
        with self.assertRaises(ValueError):
            calibrate_p_to_e_mixture(-0.1)


class EProcessTests(unittest.TestCase):
    def test_ville_crossing_hand_computed(self) -> None:
        """Power kappa=0.5, alpha=0.05 (threshold 20): p=0.01 -> e=5.
        Run 1: wealth 5 < 20, no alarm. Run 2: wealth 25 >= 20 -> alarm."""
        state = new_e_process_state(alpha=0.05, calibrator="power", kappa=0.5)
        state = update_e_process(state, run_id="r1", p_value=0.01)
        self.assertAlmostEqual(state.wealth, 5.0, places=12)
        self.assertFalse(state.rejected)
        state = update_e_process(state, run_id="r2", p_value=0.01)
        self.assertAlmostEqual(state.wealth, 25.0, places=12)
        self.assertTrue(state.rejected)

    def test_rejection_is_irreversible(self) -> None:
        """After the alarm (e=50, wealth 50), two null runs (p=1 -> e=0.5)
        drop wealth to 12.5 < 20 but the rejected flag must latch (safe
        testing semantics)."""
        state = new_e_process_state(alpha=0.05, calibrator="power", kappa=0.5)
        state = update_e_process(state, run_id="r1", p_value=0.0001)  # e=50
        self.assertTrue(state.rejected)
        state = update_e_process(state, run_id="r2", p_value=1.0)
        state = update_e_process(state, run_id="r3", p_value=1.0)
        self.assertAlmostEqual(state.wealth, 12.5, places=9)
        self.assertLess(state.wealth, state.threshold)
        self.assertTrue(state.rejected)

    def test_null_history_shrinks_wealth(self) -> None:
        """Repeated p=1 runs multiply wealth by 1/2 each: no alarm ever."""
        state = new_e_process_state(alpha=0.05, calibrator="power", kappa=0.5)
        for index in range(5):
            state = update_e_process(state, run_id=f"r{index}", p_value=1.0)
        self.assertAlmostEqual(state.wealth, 0.5**5, places=12)
        self.assertFalse(state.rejected)

    def test_duplicate_run_id_rejected(self) -> None:
        state = new_e_process_state()
        state = update_e_process(state, run_id="r1", p_value=0.5)
        with self.assertRaises(ValueError):
            update_e_process(state, run_id="r1", p_value=0.5)

    def test_state_construction_validation(self) -> None:
        with self.assertRaises(ValueError):
            new_e_process_state(alpha=0.0)
        with self.assertRaises(ValueError):
            new_e_process_state(calibrator="bogus")
        with self.assertRaises(ValueError):
            new_e_process_state(calibrator="power", kappa=2.0)
        with self.assertRaises(ValueError):
            new_e_process_state(calibrator="mixture", kappa=0.5)

    def test_state_round_trips_through_dict(self) -> None:
        state = new_e_process_state(alpha=0.05, calibrator="power", kappa=0.5)
        state = update_e_process(state, run_id="r1", p_value=0.2)
        payload = state.as_dict()
        self.assertEqual(payload["artifact_type"], "sequential_regression_monitor")
        self.assertEqual(payload["run_count"], 1)
        self.assertIn("never customer accuracy", payload["claim_boundary"])


def _artifact(path: Path, rows: list[tuple[str, int, int, int]]) -> None:
    payload = {
        "artifact_type": "extraction_quality_report",
        "fixtures": [
            {
                "fixture_id": fixture_id,
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn,
            }
            for fixture_id, tp, fp, fn in rows
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


class MonitorCliTests(unittest.TestCase):
    def test_alarm_after_repeated_regressions_and_latching(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.json"
            regressed = Path(tmp) / "regressed.json"
            state = Path(tmp) / "monitor.json"
            _artifact(base, [(f"f{i}", 1, 0, 0) for i in range(10)])
            _artifact(regressed, [(f"f{i}", 1, 1, 0) for i in range(10)])
            # p_less = 1/1024 -> mixture e >> 20: single run should alarm.
            first = main(
                [
                    "--baseline",
                    str(base),
                    "--candidate",
                    str(regressed),
                    "--state",
                    str(state),
                    "--run-id",
                    "bump-1",
                ]
            )
            self.assertEqual(first, 1)
            payload = json.loads(state.read_text(encoding="utf-8"))
            self.assertTrue(payload["rejected"])
            # A perfectly clean follow-up cannot un-reject (irreversible).
            second = main(
                [
                    "--baseline",
                    str(base),
                    "--candidate",
                    str(base),
                    "--state",
                    str(state),
                    "--run-id",
                    "bump-2",
                ]
            )
            self.assertEqual(second, 1)

    def test_null_runs_accumulate_without_alarm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.json"
            state = Path(tmp) / "monitor.json"
            _artifact(base, [(f"f{i}", 1, 0, 0) for i in range(10)])
            for index in range(3):
                exit_code = main(
                    [
                        "--baseline",
                        str(base),
                        "--candidate",
                        str(base),
                        "--state",
                        str(state),
                        "--run-id",
                        f"clean-{index}",
                    ]
                )
                self.assertEqual(exit_code, 0)
            payload = json.loads(state.read_text(encoding="utf-8"))
            self.assertEqual(payload["run_count"], 3)
            self.assertFalse(payload["rejected"])
            self.assertLess(payload["wealth"], 1.0)


if __name__ == "__main__":
    unittest.main()
