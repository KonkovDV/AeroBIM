"""Betting e-values for the regression monitor (Wave R, Jul 2026).

Anchors: Waudby-Smith & Ramdas (JRSS-B 2024 read paper) — testing/estimation
by betting on bounded observations; Shafer 2021 (testing by betting);
truncation motivated by arXiv 2602.08888 (Feb 2026) — almost-sure null
bankruptcy of aggressive strategies. Claim boundary: fixture regression
history only (RT-001).
"""

from __future__ import annotations

import itertools
import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.sequential_inference import (
    betting_evalue_one_sided,
    new_e_process_state,
    update_e_process,
    update_e_process_with_evalue,
)
from aerobim.tools.sequential_regression_monitor import main


class BettingEvalueTests(unittest.TestCase):
    def test_exact_martingale_under_symmetric_null(self) -> None:
        """Hand-enumerated: d_t in {-1,+1} equiprobable (boundary null).
        All 8 length-3 sequences worked out by hand give wealths
        (1, 1, 1, 1, 0.5, 0.5, 0.75, 2.25) — the average is exactly 1,
        i.e. the truncated-aGRAPA wealth is a genuine martingale."""
        wealths = [
            betting_evalue_one_sided(list(diffs)).e_value
            for diffs in itertools.product((-1.0, 1.0), repeat=3)
        ]
        self.assertAlmostEqual(sum(wealths) / len(wealths), 1.0, places=9)
        self.assertAlmostEqual(max(wealths), 2.25, places=9)

    def test_sustained_worst_case_regression_grows_geometrically(self) -> None:
        """All diffs = -1: after the burn-in round the bet saturates at the
        cap, each factor is 1.5 => W = 1.5^(n-1) (hand-derived)."""
        result = betting_evalue_one_sided([-1.0] * 10)
        self.assertAlmostEqual(result.e_value, 1.5**9, places=9)
        self.assertEqual(result.final_lambda, -1.0)

    def test_uniform_third_regression_factor_seven_sixths(self) -> None:
        """diffs = -1/3 => x = 1/3; capped bet gives factor 1 + 1/6 per
        post-burn-in round => W = (7/6)^(n-1) (hand-derived)."""
        result = betting_evalue_one_sided([-1 / 3] * 10)
        self.assertAlmostEqual(result.e_value, (7 / 6) ** 9, places=9)

    def test_clean_run_keeps_wealth_exactly_one(self) -> None:
        """Zero diffs => x = 1/2 => every factor is exactly 1. Operational
        edge over p-calibration: clean runs cause no wealth erosion
        (mixture calibrator halves wealth on p=1)."""
        result = betting_evalue_one_sided([0.0] * 8)
        self.assertEqual(result.e_value, 1.0)

    def test_improvement_never_generates_evidence(self) -> None:
        """Positive diffs: one-sided rule clips the bet to 0 => W = 1."""
        result = betting_evalue_one_sided([1.0, 0.5, 1.0, 0.75])
        self.assertEqual(result.e_value, 1.0)
        self.assertEqual(result.final_lambda, 0.0)

    def test_first_round_never_bets(self) -> None:
        """Predictability: with a single observation W must equal 1."""
        self.assertEqual(betting_evalue_one_sided([-1.0]).e_value, 1.0)

    def test_invalid_inputs_rejected(self) -> None:
        with self.assertRaises(ValueError):
            betting_evalue_one_sided([])
        with self.assertRaises(ValueError):
            betting_evalue_one_sided([1.5])
        with self.assertRaises(ValueError):
            betting_evalue_one_sided([float("nan")])
        with self.assertRaises(ValueError):
            betting_evalue_one_sided([0.0], lambda_cap=0.0)
        with self.assertRaises(ValueError):
            betting_evalue_one_sided([0.0], lambda_cap=2.0)


class BettingEProcessIntegrationTests(unittest.TestCase):
    def test_betting_state_accepts_direct_evalues_and_latches(self) -> None:
        state = new_e_process_state(alpha=0.05, calibrator="betting")
        state = update_e_process_with_evalue(state, run_id="r1", e_value=30.0)
        self.assertTrue(state.rejected)
        # Markov companion p = min(1, 1/e).
        self.assertAlmostEqual(state.history[0].p_value, 1 / 30, places=12)

    def test_source_mixing_is_forbidden_both_ways(self) -> None:
        betting_state = new_e_process_state(calibrator="betting")
        with self.assertRaises(ValueError):
            update_e_process(betting_state, run_id="r1", p_value=0.01)
        mixture_state = new_e_process_state(calibrator="mixture")
        with self.assertRaises(ValueError):
            update_e_process_with_evalue(mixture_state, run_id="r1", e_value=2.0)

    def test_invalid_direct_evalues_rejected(self) -> None:
        state = new_e_process_state(calibrator="betting")
        with self.assertRaises(ValueError):
            update_e_process_with_evalue(state, run_id="r1", e_value=-1.0)
        with self.assertRaises(ValueError):
            update_e_process_with_evalue(state, run_id="r1", e_value=float("inf"))

    def test_betting_state_rejects_kappa(self) -> None:
        with self.assertRaises(ValueError):
            new_e_process_state(calibrator="betting", kappa=0.5)


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


class BettingMonitorCliTests(unittest.TestCase):
    def test_betting_run_produces_hand_computed_evalue(self) -> None:
        """Per-fixture F1 drop 1 -> 2/3 gives diff = -1/3 on all 10
        fixtures => e-value (7/6)^9 ~= 4.03; single run stays below the
        Ville threshold 20 (unlike the mixture calibrator on the same
        data) — the complementary power profile, recorded honestly."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.json"
            regressed = Path(tmp) / "regressed.json"
            state = Path(tmp) / "monitor.json"
            _artifact(base, [(f"f{i}", 1, 0, 0) for i in range(10)])
            _artifact(regressed, [(f"f{i}", 1, 1, 0) for i in range(10)])
            exit_code = main(
                [
                    "--baseline",
                    str(base),
                    "--candidate",
                    str(regressed),
                    "--state",
                    str(state),
                    "--run-id",
                    "bump-1",
                    "--calibrator",
                    "betting",
                ]
            )
            self.assertEqual(exit_code, 0)
            payload = json.loads(state.read_text(encoding="utf-8"))
            self.assertEqual(payload["calibrator"], "betting")
            self.assertAlmostEqual(payload["wealth"], (7 / 6) ** 9, places=9)
            self.assertFalse(payload["rejected"])
            # Two more identical regressions cross 20: ((7/6)^9)^3 ~= 65.6.
            for run in ("bump-2", "bump-3"):
                exit_code = main(
                    [
                        "--baseline",
                        str(base),
                        "--candidate",
                        str(regressed),
                        "--state",
                        str(state),
                        "--run-id",
                        run,
                        "--calibrator",
                        "betting",
                    ]
                )
            self.assertEqual(exit_code, 1)
            payload = json.loads(state.read_text(encoding="utf-8"))
            self.assertTrue(payload["rejected"])

    def test_clean_betting_runs_do_not_erode_wealth(self) -> None:
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
                        "--calibrator",
                        "betting",
                    ]
                )
                self.assertEqual(exit_code, 0)
            payload = json.loads(state.read_text(encoding="utf-8"))
            self.assertEqual(payload["wealth"], 1.0)
            self.assertFalse(payload["rejected"])


if __name__ == "__main__":
    unittest.main()
