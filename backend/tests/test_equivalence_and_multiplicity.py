"""Equivalence TOST + Holm multiplicity control (Wave M, Jul 2026).

Anchors: Schuirmann 1987 (TOST); Berger & Hsu 1996 (CI-inclusion form);
Lakens 2017 (SESOI margins, 90% CI at alpha=0.05); Robinson & Froese 2004
(bootstrap TOST); Holm 1979 (step-down FWER); Dror et al. 2017 TACL
(multiple comparisons practice in NLP); Phipson & Smyth 2010 (add-one,
never-zero p). Claim boundary: verdicts describe fixture corpora only
(RT-001); "equivalent" holds only at the pre-specified margin.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.eval_statistics import (
    FixtureCounts,
    equivalence_tost,
    holm_bonferroni,
)
from aerobim.tools.compare_extraction_runs import compare_extraction_runs, main

_WORSE = FixtureCounts(true_positives=1, false_positives=1, false_negatives=0)  # F1=2/3
_BETTER = FixtureCounts(true_positives=1, false_positives=0, false_negatives=0)  # F1=1


class EquivalenceTostTests(unittest.TestCase):
    def test_identical_systems_equivalent_within_any_positive_margin(self) -> None:
        """A == B pairwise: every bootstrap diff is exactly 0, so the 90% CI
        is degenerate at 0 and lies inside (-m, m) for any m > 0."""
        fixtures = [_WORSE, _BETTER, _WORSE, _BETTER, _WORSE]
        result = equivalence_tost(fixtures, list(fixtures), margin=0.01, replicates=200)
        self.assertEqual(result.observed_diff, 0.0)
        self.assertEqual(result.ci_lower, 0.0)
        self.assertEqual(result.ci_upper, 0.0)
        self.assertTrue(result.stable)
        self.assertTrue(result.equivalent)
        # Add-one: even with zero tail mass, p = 1/(B+1), never 0.
        self.assertAlmostEqual(result.p_lower, 1 / 201, places=12)
        self.assertAlmostEqual(result.p_upper, 1 / 201, places=12)
        self.assertAlmostEqual(result.p_tost, 1 / 201, places=12)

    def test_uniform_one_third_improvement_not_equivalent_at_tight_margin(self) -> None:
        """B better by exactly 1/3 on every pair: every bootstrap resample
        yields diff = 1/3, so the CI is degenerate at 1/3 >> margin 0.05."""
        result = equivalence_tost([_WORSE] * 8, [_BETTER] * 8, margin=0.05, replicates=200)
        self.assertAlmostEqual(result.observed_diff, 1 / 3, places=12)
        self.assertAlmostEqual(result.ci_lower, 1 / 3, places=12)
        self.assertAlmostEqual(result.ci_upper, 1 / 3, places=12)
        self.assertFalse(result.equivalent)
        # Upper tail holds all B resamples: p_upper = (200+1)/(200+1) = 1.
        self.assertEqual(result.p_upper, 1.0)
        self.assertEqual(result.p_tost, 1.0)

    def test_same_shift_equivalent_at_generous_margin(self) -> None:
        """The same 1/3 shift IS equivalent when the pre-specified SESOI is
        larger than the shift — the verdict is margin-relative by design."""
        result = equivalence_tost([_WORSE] * 8, [_BETTER] * 8, margin=0.5, replicates=200)
        self.assertTrue(result.equivalent)

    def test_too_few_pairs_withholds_equivalence(self) -> None:
        """n=3 < stability floor: fail-closed — never certify equivalence
        from a corpus too small to bound the difference."""
        result = equivalence_tost([_WORSE] * 3, [_WORSE] * 3, margin=0.5, replicates=100)
        self.assertFalse(result.stable)
        self.assertFalse(result.equivalent)

    def test_determinism_given_seed(self) -> None:
        a = [_WORSE, _BETTER] * 4
        b = [_BETTER, _WORSE] * 4
        first = equivalence_tost(a, b, margin=0.1, replicates=300, seed=7)
        second = equivalence_tost(a, b, margin=0.1, replicates=300, seed=7)
        self.assertEqual(first, second)

    def test_invalid_inputs_rejected(self) -> None:
        with self.assertRaises(ValueError):
            equivalence_tost([_WORSE], [_BETTER], margin=0.0)
        with self.assertRaises(ValueError):
            equivalence_tost([_WORSE], [_BETTER], margin=-0.1)
        with self.assertRaises(ValueError):
            equivalence_tost([_WORSE], [_BETTER, _BETTER], margin=0.1)
        with self.assertRaises(ValueError):
            equivalence_tost([], [], margin=0.1)
        with self.assertRaises(ValueError):
            equivalence_tost([_WORSE], [_BETTER], margin=0.1, alpha=0.5)
        with self.assertRaises(ValueError):
            equivalence_tost([_WORSE], [_BETTER], margin=0.1, metric="bogus")


class HolmBonferroniTests(unittest.TestCase):
    def test_hand_computed_holm_example(self) -> None:
        """Holm 1979 worked by hand for m=4, p = (0.01, 0.02, 0.03, 0.20):
        adj = (4*0.01, 3*0.02, 2*0.03, 1*0.20) = (0.04, 0.06, 0.06, 0.20)
        after the running-max monotonicity step."""
        result = holm_bonferroni({"a": 0.01, "b": 0.02, "c": 0.03, "d": 0.20})
        adjusted = result.as_dict()["adjusted_p"]
        self.assertEqual(adjusted, {"a": 0.04, "b": 0.06, "c": 0.06, "d": 0.2})
        self.assertEqual(
            result.reject,
            {"a": True, "b": False, "c": False, "d": False},
        )

    def test_monotonicity_running_max(self) -> None:
        """p=(0.04, 0.05): naive step-down gives (0.08, 0.05) — the running
        max must restore monotone order to (0.08, 0.08)."""
        result = holm_bonferroni({"x": 0.04, "y": 0.05})
        self.assertEqual(result.as_dict()["adjusted_p"], {"x": 0.08, "y": 0.08})

    def test_adjusted_p_capped_at_one(self) -> None:
        result = holm_bonferroni({"x": 0.6, "y": 0.9})
        self.assertEqual(result.adjusted_p["x"], 1.0)
        self.assertEqual(result.adjusted_p["y"], 1.0)

    def test_single_test_unchanged(self) -> None:
        result = holm_bonferroni({"only": 0.03})
        self.assertEqual(result.adjusted_p, {"only": 0.03})
        self.assertTrue(result.reject["only"])

    def test_invalid_inputs_rejected(self) -> None:
        with self.assertRaises(ValueError):
            holm_bonferroni({})
        with self.assertRaises(ValueError):
            holm_bonferroni({"bad": 1.5})
        with self.assertRaises(ValueError):
            holm_bonferroni({"bad": -0.1})


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


class CompareRunsEquivalenceCliTests(unittest.TestCase):
    def test_artifact_carries_holm_family_and_tost_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.json"
            cand = Path(tmp) / "cand.json"
            rows = [(f"f{i}", 1, 0, 0) for i in range(10)]
            _artifact(base, rows)
            _artifact(cand, rows)
            result = compare_extraction_runs(base, cand, equivalence_margin=0.02)
        self.assertEqual(result["schema_version"], "1.1.0")
        self.assertEqual(result["multiple_comparisons"]["method"], "holm_bonferroni")
        self.assertEqual(result["multiple_comparisons"]["family_size"], 4)
        macro = result["comparisons"]["macro_f1"]
        self.assertIn("holm_adjusted_p", macro)
        self.assertFalse(macro["significant_after_holm"])
        self.assertTrue(macro["equivalence"]["equivalent"])
        self.assertIn("pre-specified margin", result["claim_boundary"])

    def test_no_margin_means_no_equivalence_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.json"
            cand = Path(tmp) / "cand.json"
            rows = [(f"f{i}", 1, 0, 0) for i in range(6)]
            _artifact(base, rows)
            _artifact(cand, rows)
            result = compare_extraction_runs(base, cand)
        self.assertIsNone(result["equivalence_margin"])
        self.assertNotIn("equivalence", result["comparisons"]["macro_f1"])

    def test_fail_on_nonequivalence_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.json"
            same = Path(tmp) / "same.json"
            shifted = Path(tmp) / "shifted.json"
            _artifact(base, [(f"f{i}", 1, 0, 0) for i in range(10)])
            _artifact(same, [(f"f{i}", 1, 0, 0) for i in range(10)])
            # Uniform 1/3 macro-F1 drop: far outside a 0.02 margin.
            _artifact(shifted, [(f"f{i}", 1, 1, 0) for i in range(10)])
            passing = main(
                [
                    "--baseline",
                    str(base),
                    "--candidate",
                    str(same),
                    "--equivalence-margin",
                    "0.02",
                    "--fail-on-nonequivalence",
                ]
            )
            failing = main(
                [
                    "--baseline",
                    str(base),
                    "--candidate",
                    str(shifted),
                    "--equivalence-margin",
                    "0.02",
                    "--fail-on-nonequivalence",
                ]
            )
        self.assertEqual(passing, 0)
        self.assertEqual(failing, 1)

    def test_nonequivalence_gate_requires_margin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.json"
            _artifact(base, [("a", 1, 0, 0)])
            with self.assertRaises(SystemExit):
                main(
                    [
                        "--baseline",
                        str(base),
                        "--candidate",
                        str(base),
                        "--fail-on-nonequivalence",
                    ]
                )


if __name__ == "__main__":
    unittest.main()
