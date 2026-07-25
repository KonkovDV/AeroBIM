"""Paired significance testing for system comparison (Wave L, Jul 2026).

Anchors: Dror et al. 2018 (significance in NLP); Zmigrod et al. 2022 (exact
paired permutation); Phipson & Smyth 2010 (add-one, never-zero p);
statsforevals protocol; arXiv 2511.06701 (harness-enforced rigor).
Claim boundary: verdicts describe fixture corpora only (RT-001);
non-significant != equivalent.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.eval_statistics import (
    FixtureCounts,
    paired_bootstrap_diff_ci,
    paired_permutation_test,
)
from aerobim.tools.compare_extraction_runs import compare_extraction_runs, main

_WORSE = FixtureCounts(true_positives=1, false_positives=1, false_negatives=0)  # F1=2/3
_BETTER = FixtureCounts(true_positives=1, false_positives=0, false_negatives=0)  # F1=1


class PairedPermutationExactTests(unittest.TestCase):
    def test_hand_enumerated_two_pair_case(self) -> None:
        """n=2, B better by 1/3 on each pair: masks 00/11 give |diff|=1/3,
        masks 01/10 give 0 => exact p = 2/4 = 0.5 (enumerated by hand)."""
        result = paired_permutation_test([_WORSE, _WORSE], [_BETTER, _BETTER], metric="macro_f1")
        self.assertTrue(result.exact)
        self.assertEqual(result.permutations, 4)
        self.assertAlmostEqual(result.observed_diff, 1 / 3, places=12)
        self.assertEqual(result.p_value, 0.5)

    def test_single_pair_p_is_one(self) -> None:
        result = paired_permutation_test([_WORSE], [_BETTER], metric="macro_f1")
        self.assertTrue(result.exact)
        self.assertEqual(result.p_value, 1.0)

    def test_identical_systems_p_is_one(self) -> None:
        fixtures = [_WORSE, _BETTER, _WORSE, _BETTER]
        result = paired_permutation_test(fixtures, list(fixtures), metric="macro_f1")
        self.assertEqual(result.observed_diff, 0.0)
        self.assertEqual(result.p_value, 1.0)

    def test_consistent_improvement_over_ten_pairs_is_significant(self) -> None:
        """Ten aligned pairs, B uniformly better: only the all-flip and
        no-flip masks reach |observed| => exact p = 2/1024 < 0.05."""
        result = paired_permutation_test([_WORSE] * 10, [_BETTER] * 10, metric="macro_f1")
        self.assertTrue(result.exact)
        self.assertAlmostEqual(result.p_value, 2 / 1024, places=12)
        self.assertLess(result.p_value, 0.05)

    def test_monte_carlo_path_is_deterministic_and_never_zero(self) -> None:
        a = [_WORSE] * 13
        b = [_BETTER] * 13
        first = paired_permutation_test(a, b, metric="macro_f1", replicates=999, seed=5)
        second = paired_permutation_test(a, b, metric="macro_f1", replicates=999, seed=5)
        self.assertFalse(first.exact)
        self.assertEqual(first, second)
        self.assertGreater(first.p_value, 0.0)  # Phipson & Smyth add-one

    def test_length_mismatch_and_unknown_metric_rejected(self) -> None:
        with self.assertRaises(ValueError):
            paired_permutation_test([_WORSE], [_BETTER, _BETTER])
        with self.assertRaises(ValueError):
            paired_permutation_test([_WORSE], [_BETTER], metric="bogus")


class PairedDiffCiTests(unittest.TestCase):
    def test_identical_systems_ci_degenerate_at_zero(self) -> None:
        fixtures = [_WORSE, _BETTER, _WORSE]
        ci = paired_bootstrap_diff_ci(fixtures, list(fixtures), metric="macro_f1")
        self.assertEqual(ci.point, 0.0)
        self.assertEqual(ci.lower, 0.0)
        self.assertEqual(ci.upper, 0.0)

    def test_uniform_improvement_ci_excludes_zero(self) -> None:
        ci = paired_bootstrap_diff_ci(
            [_WORSE] * 8, [_BETTER] * 8, metric="macro_f1", replicates=300, seed=11
        )
        self.assertAlmostEqual(ci.point, 1 / 3, places=12)
        self.assertGreater(ci.lower, 0.0)
        self.assertEqual(ci.method, "paired_cluster_percentile_bootstrap")


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


class CompareExtractionRunsTests(unittest.TestCase):
    def test_comparison_artifact_shape_and_significance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.json"
            cand = Path(tmp) / "cand.json"
            rows_base = [(f"f{i}", 1, 1, 0) for i in range(10)]
            rows_cand = [(f"f{i}", 1, 0, 0) for i in range(10)]
            _artifact(base, rows_base)
            _artifact(cand, rows_cand)
            result = compare_extraction_runs(base, cand)
        self.assertEqual(result["artifact_type"], "extraction_paired_comparison")
        self.assertEqual(result["n_pairs"], 10)
        macro = result["comparisons"]["macro_f1"]
        self.assertTrue(macro["significant"])
        self.assertGreater(macro["permutation_test"]["observed_diff"], 0)
        self.assertGreater(macro["diff_ci"]["lower"], 0)
        self.assertIn("never customer accuracy", result["claim_boundary"])

    def test_fail_on_regression_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.json"
            cand = Path(tmp) / "cand.json"
            # Candidate is uniformly worse -> significant regression.
            _artifact(base, [(f"f{i}", 1, 0, 0) for i in range(10)])
            _artifact(cand, [(f"f{i}", 1, 1, 0) for i in range(10)])
            exit_code = main(
                [
                    "--baseline",
                    str(base),
                    "--candidate",
                    str(cand),
                    "--fail-on-regression",
                ]
            )
        self.assertEqual(exit_code, 1)

    def test_disjoint_fixture_ids_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.json"
            cand = Path(tmp) / "cand.json"
            _artifact(base, [("a", 1, 0, 0)])
            _artifact(cand, [("b", 1, 0, 0)])
            with self.assertRaises(ValueError):
                compare_extraction_runs(base, cand)


if __name__ == "__main__":
    unittest.main()
