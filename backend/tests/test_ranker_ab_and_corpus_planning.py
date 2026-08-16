"""Waves P & Q: ranker A/B comparison + adjudication corpus planning.

Anchors: Miller 2024 (arXiv 2411.00640) paired design + eval power analysis;
Wilson 1927; Brown, Cai & DasGupta 2001 (Wilson recommended); exact binomial
test power via math.comb; McSherry & Najork 2008 (per-case tie-aware nDCG).
Claim boundary: fixture verdicts only (RT-001).
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.eval_statistics import (
    paired_scalar_bootstrap_diff_ci,
    paired_scalar_permutation_test,
)
from aerobim.domain.study_design import (
    binomial_power_one_sided,
    required_n_for_power,
    required_n_for_wilson_halfwidth,
    wilson_interval,
)
from aerobim.tools.compare_ranker_profiles import compare_ranker_profiles, main
from aerobim.tools.plan_adjudication_corpus import plan_adjudication_corpus


class PairedScalarPermutationTests(unittest.TestCase):
    def test_hand_enumerated_two_pairs(self) -> None:
        """diffs (0.5, 0.5): masks 00→+0.5, 01/10→0, 11→−0.5;
        two-sided extreme = {00, 11} => p = 2/4."""
        result = paired_scalar_permutation_test([0.0, 0.0], [0.5, 0.5])
        self.assertTrue(result.exact)
        self.assertAlmostEqual(result.observed_diff, 0.5, places=12)
        self.assertEqual(result.p_value, 0.5)

    def test_uniform_improvement_ten_pairs(self) -> None:
        result = paired_scalar_permutation_test([0.0] * 10, [0.1] * 10)
        self.assertAlmostEqual(result.p_value, 2 / 1024, places=12)

    def test_one_sided_less_hand_enumerated(self) -> None:
        """diffs (−0.5, −0.5): only mask 00 gives −0.5 <= observed => 1/4."""
        result = paired_scalar_permutation_test([1.0, 1.0], [0.5, 0.5], alternative="less")
        self.assertEqual(result.p_value, 0.25)

    def test_identical_values_p_one(self) -> None:
        result = paired_scalar_permutation_test([0.3, 0.7], [0.3, 0.7])
        self.assertEqual(result.observed_diff, 0.0)
        self.assertEqual(result.p_value, 1.0)

    def test_invalid_inputs_rejected(self) -> None:
        with self.assertRaises(ValueError):
            paired_scalar_permutation_test([], [])
        with self.assertRaises(ValueError):
            paired_scalar_permutation_test([1.0], [1.0, 2.0])
        with self.assertRaises(ValueError):
            paired_scalar_permutation_test([float("nan")], [1.0])
        with self.assertRaises(ValueError):
            paired_scalar_permutation_test([0.0] * 13, [1.0] * 13, replicates=0)
        with self.assertRaises(ValueError):
            paired_scalar_permutation_test([0.0], [1.0], alternative="bogus")

    def test_bootstrap_ci_degenerate_on_constant_diffs(self) -> None:
        ci = paired_scalar_bootstrap_diff_ci([0.0] * 6, [0.5] * 6, replicates=200)
        self.assertAlmostEqual(ci.point, 0.5, places=12)
        self.assertAlmostEqual(ci.lower, 0.5, places=12)
        self.assertAlmostEqual(ci.upper, 0.5, places=12)


def _labels(path: Path, *, scores: dict[str, float], cases: int = 10) -> None:
    """Artifact with `cases` identical cases: rel grades 2/1/0 for f1/f2/f3."""
    grades = {"f1": 2, "f2": 1, "f3": 0}
    payload = {
        "artifact_type": "ranking_quality_labels",
        "schema_version": "1.0.0",
        "dataset_id": "ab-fixture",
        "dataset_status": "draft",
        "cases": [
            {
                "case_id": f"case-{i}",
                "findings": [
                    {
                        "finding_id": fid,
                        "priority_score": scores[fid],
                        "relevance": grades[fid],
                    }
                    for fid in ("f1", "f2", "f3")
                ],
            }
            for i in range(cases)
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


class CompareRankerProfilesTests(unittest.TestCase):
    def test_flat_vs_perfect_profile_significant(self) -> None:
        """A ties everything (one tie group => nDCG < 1); B orders perfectly
        (nDCG = 1). Uniform improvement over 10 cases => exact p = 2/1024."""
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "a.json"
            b = Path(tmp) / "b.json"
            _labels(a, scores={"f1": 10, "f2": 10, "f3": 10})
            _labels(b, scores={"f1": 30, "f2": 20, "f3": 10})
            report = compare_ranker_profiles(a, b)
        full = report["comparisons"]["ndcg_full"]
        self.assertEqual(report["n_defined_pairs"], 10)
        self.assertEqual(full["mean_ndcg_b"], 1.0)
        self.assertLess(full["mean_ndcg_a"], 1.0)
        self.assertAlmostEqual(full["permutation_test"]["p_value"], round(2 / 1024, 6), places=6)
        self.assertTrue(full["significant_after_holm"])
        self.assertGreater(full["diff_ci"]["lower"], 0.0)
        self.assertEqual(report["multiple_comparisons"]["primary_metric"], "ndcg_full")

    def test_identical_profiles_not_significant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "a.json"
            b = Path(tmp) / "b.json"
            _labels(a, scores={"f1": 30, "f2": 20, "f3": 10})
            _labels(b, scores={"f1": 30, "f2": 20, "f3": 10})
            report = compare_ranker_profiles(a, b)
        full = report["comparisons"]["ndcg_full"]
        self.assertEqual(full["permutation_test"]["p_value"], 1.0)
        self.assertFalse(full["significant"])

    def test_grade_mismatch_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "a.json"
            b = Path(tmp) / "b.json"
            _labels(a, scores={"f1": 30, "f2": 20, "f3": 10})
            payload = json.loads(a.read_text(encoding="utf-8"))
            payload["cases"][0]["findings"][0]["relevance"] = 1  # tamper grade
            b.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ValueError):
                compare_ranker_profiles(a, b)

    def test_cli_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "a.json"
            b = Path(tmp) / "b.json"
            out = Path(tmp) / "report.json"
            _labels(a, scores={"f1": 10, "f2": 10, "f3": 10}, cases=6)
            _labels(b, scores={"f1": 30, "f2": 20, "f3": 10}, cases=6)
            exit_code = main(["--profile-a", str(a), "--profile-b", str(b), "--output", str(out)])
            self.assertEqual(exit_code, 0)
            written = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(written["artifact_type"], "ranker_profile_comparison")


class WilsonIntervalTests(unittest.TestCase):
    def test_classic_five_of_ten(self) -> None:
        """Textbook value: k=5, n=10, 95% Wilson = (0.2366, 0.7634);
        center is exactly 0.5 because p_hat + z^2/2n = denom/2."""
        interval = wilson_interval(5, 10)
        self.assertAlmostEqual(interval.lower, 0.2366, places=3)
        self.assertAlmostEqual(interval.upper, 0.7634, places=3)
        self.assertAlmostEqual((interval.lower + interval.upper) / 2, 0.5, places=12)

    def test_bounds_clamped_and_validated(self) -> None:
        self.assertGreaterEqual(wilson_interval(0, 10).lower, 0.0)
        self.assertLessEqual(wilson_interval(10, 10).upper, 1.0)
        with self.assertRaises(ValueError):
            wilson_interval(11, 10)
        with self.assertRaises(ValueError):
            wilson_interval(1, 0)

    def test_required_n_for_halfwidth_semantics(self) -> None:
        n = required_n_for_wilson_halfwidth(0.75, half_width=0.08)
        # Wald ballpark: p*q*z^2/h^2 = 0.1875*3.84/0.0064 ~= 112.
        self.assertTrue(90 <= n <= 130, n)
        k = round(0.75 * n)
        self.assertLessEqual(wilson_interval(k, n).half_width, 0.08)

    def test_hd4_interim_n111_reproduces_docs(self) -> None:
        # HD4-STAT-02: docs "recommended_n=111 for interim 0.60" is the planner output.
        n = required_n_for_wilson_halfwidth(0.60, half_width=0.09)
        self.assertEqual(n, 111)
        k = round(0.60 * n)
        half_width = wilson_interval(k, n).half_width
        self.assertLessEqual(half_width, 0.09)
        self.assertAlmostEqual(half_width, 0.0895, places=4)


class ExactBinomialPowerTests(unittest.TestCase):
    def test_hand_computed_critical_value_n20(self) -> None:
        """Bin(20, 0.5): P(K>=15) = 21700/2^20 ~= 0.0207 <= 0.05 while
        P(K>=14) ~= 0.0577 > 0.05 => critical_k = 15 (tail summed by hand:
        15504+4845+1140+190+20+1 = 21700)."""
        design = binomial_power_one_sided(n=20, p0=0.5, p_true=0.8)
        self.assertEqual(design.critical_k, 15)
        self.assertAlmostEqual(design.attained_alpha, 21700 / 1048576, places=12)
        # Known reference: P(K>=15 | n=20, p=0.8) ~= 0.804.
        self.assertAlmostEqual(design.power, 0.804, delta=0.005)

    def test_required_n_matches_normal_approximation_ballpark(self) -> None:
        """Pilot defaults (p0=0.60, p1=0.75, alpha=0.05, power=0.8): normal
        approximation gives n ~= 61; exact smallest n must be nearby and
        n-1 must fail the power target (smallest-n semantics)."""
        design = required_n_for_power(p0=0.60, p_true=0.75)
        self.assertTrue(50 <= design.n <= 80, design.n)
        self.assertGreaterEqual(design.power, 0.8)
        previous = binomial_power_one_sided(n=design.n - 1, p0=0.60, p_true=0.75)
        self.assertLess(previous.power, 0.8)

    def test_invalid_inputs_rejected(self) -> None:
        with self.assertRaises(ValueError):
            binomial_power_one_sided(n=0, p0=0.5, p_true=0.8)
        with self.assertRaises(ValueError):
            binomial_power_one_sided(n=10, p0=0.8, p_true=0.6)  # wrong direction
        with self.assertRaises(ValueError):
            required_n_for_power(p0=0.6, p_true=0.75, power=1.0)


class PlanAdjudicationCorpusTests(unittest.TestCase):
    def test_plan_artifact_shape_and_decision_preview(self) -> None:
        plan = plan_adjudication_corpus()
        self.assertEqual(plan["artifact_type"], "adjudication_corpus_plan")
        self.assertEqual(
            plan["recommended_n"],
            max(plan["power_design"]["n"], plan["wilson_width_n"]),
        )
        preview = {row["planning_rate"]: row for row in plan["decision_preview_at_recommended_n"]}
        # Observing exactly the threshold rate can never demonstrate it...
        self.assertFalse(preview[0.6]["demonstrates_threshold"])
        # ...while the expected rate at the recommended n must.
        self.assertTrue(preview[0.75]["demonstrates_threshold"])
        self.assertIn("RT-001", plan["claim_boundary"])

    def test_expected_below_threshold_rejected(self) -> None:
        with self.assertRaises(ValueError):
            plan_adjudication_corpus(threshold=0.6, expected_precision=0.55)


if __name__ == "__main__":
    unittest.main()
