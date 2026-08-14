"""Evaluation statistics: bootstrap CIs + inter-annotator agreement (Wave K).

Anchors (Jul 2026): NeurIPS paper checklist (error bars mandatory, method
stated); ACL Responsible-NLP checklist (bootstrap 1000 resamples, 95% CI);
Efron & Tibshirani 1993 (percentile bootstrap); Cohen 1960 (kappa);
Krippendorff 2019 (nominal alpha, coincidence matrix). Claim boundary:
CIs/agreement quantify fixture-label uncertainty; never upgrade fixture
evidence to customer evidence (RT-001).
"""

from __future__ import annotations

import unittest

from aerobim.domain.eval_statistics import (
    FixtureCounts,
    agreement_artifact,
    cluster_bootstrap_cis,
    cohen_kappa,
    krippendorff_alpha_nominal,
)


def _fixtures() -> list[FixtureCounts]:
    return [
        FixtureCounts(true_positives=8, false_positives=2, false_negatives=1),
        FixtureCounts(true_positives=5, false_positives=0, false_negatives=3),
        FixtureCounts(true_positives=9, false_positives=1, false_negatives=0),
        FixtureCounts(true_positives=4, false_positives=3, false_negatives=2),
        FixtureCounts(true_positives=7, false_positives=1, false_negatives=1),
        FixtureCounts(true_positives=6, false_positives=2, false_negatives=2),
    ]


class ClusterBootstrapTests(unittest.TestCase):
    def test_deterministic_given_seed(self) -> None:
        first = cluster_bootstrap_cis(_fixtures(), replicates=200, seed=42)
        second = cluster_bootstrap_cis(_fixtures(), replicates=200, seed=42)
        self.assertEqual(first, second)

    def test_different_seed_changes_replicates_not_point(self) -> None:
        a = cluster_bootstrap_cis(_fixtures(), replicates=200, seed=1)
        b = cluster_bootstrap_cis(_fixtures(), replicates=200, seed=2)
        self.assertEqual(a["micro_f1"].point, b["micro_f1"].point)

    def test_interval_brackets_point_estimate(self) -> None:
        cis = cluster_bootstrap_cis(_fixtures(), replicates=500, seed=7)
        for ci in cis.values():
            self.assertLessEqual(ci.lower, ci.point + 1e-9, msg=ci.metric)
            self.assertGreaterEqual(ci.upper, ci.point - 1e-9, msg=ci.metric)
            self.assertLessEqual(ci.lower, ci.upper)

    def test_perfect_fixtures_yield_degenerate_interval_at_one(self) -> None:
        perfect = [
            FixtureCounts(true_positives=5, false_positives=0, false_negatives=0) for _ in range(6)
        ]
        cis = cluster_bootstrap_cis(perfect, replicates=100, seed=3)
        self.assertEqual(cis["micro_f1"].lower, 1.0)
        self.assertEqual(cis["micro_f1"].upper, 1.0)

    def test_small_cluster_count_flagged_unstable(self) -> None:
        cis = cluster_bootstrap_cis(_fixtures()[:2], replicates=100, seed=3)
        self.assertFalse(cis["macro_f1"].stable)
        stable = cluster_bootstrap_cis(_fixtures(), replicates=100, seed=3)
        self.assertTrue(stable["macro_f1"].stable)


class CohenKappaTests(unittest.TestCase):
    def test_perfect_agreement_is_one(self) -> None:
        self.assertEqual(cohen_kappa(["a", "b", "a"], ["a", "b", "a"]), 1.0)

    def test_hand_computed_value(self) -> None:
        # po=4/5=0.8; pe=(3/5*4/5)+(2/5*1/5)=0.56; kappa=(0.8-0.56)/0.44=0.545454...
        kappa = cohen_kappa(["1", "1", "2", "2", "1"], ["1", "1", "2", "1", "1"])
        self.assertAlmostEqual(kappa, 0.24 / 0.44, places=9)

    def test_length_mismatch_rejected(self) -> None:
        with self.assertRaises(ValueError):
            cohen_kappa(["a"], ["a", "b"])


class KrippendorffAlphaTests(unittest.TestCase):
    def test_perfect_agreement_is_one(self) -> None:
        units = [{"a": "x", "b": "x"}, {"a": "y", "b": "y"}]
        self.assertEqual(krippendorff_alpha_nominal(units), 1.0)

    def test_hand_computed_nominal_value(self) -> None:
        # Coders A,B over 5 units: A=[1,2,3,3,2], B=[1,2,3,3,1].
        # Coincidences: o11=2, o22=2, o33=4, o12=o21=1; n=10; n_c=(3,3,4).
        # alpha = 1 - (n-1)*sum_offdiag / (n^2 - sum n_c^2)
        #       = 1 - 9*2 / (100-34) = 1 - 18/66 = 0.727272...
        units = [
            {"A": "1", "B": "1"},
            {"A": "2", "B": "2"},
            {"A": "3", "B": "3"},
            {"A": "3", "B": "3"},
            {"A": "2", "B": "1"},
        ]
        self.assertAlmostEqual(krippendorff_alpha_nominal(units), 1 - 18 / 66, places=9)

    def test_missing_labels_are_tolerated(self) -> None:
        units = [
            {"A": "x", "B": "x", "C": None},
            {"A": "y", "B": "y", "C": "y"},
            {"A": "x", "B": None, "C": None},  # unpairable — excluded
        ]
        alpha = krippendorff_alpha_nominal(units)
        self.assertEqual(alpha, 1.0)

    def test_all_unpairable_rejected(self) -> None:
        with self.assertRaises(ValueError):
            krippendorff_alpha_nominal([{"A": "x"}, {"B": "y"}])


class AgreementArtifactTests(unittest.TestCase):
    def test_two_annotator_artifact_feeds_rt001_gate(self) -> None:
        from aerobim.domain.architecture import (
            PrecisionClaim,
            precision_claim_publishable_with_agreement,
        )

        units = [
            {"ann1": "TP", "ann2": "TP"},
            {"ann1": "FP", "ann2": "FP"},
            {"ann1": "TP", "ann2": "TP"},
            {"ann1": "FP", "ann2": "TP"},
            {"ann1": "TP", "ann2": "TP"},
            {"ann1": "FP", "ann2": "FP"},
        ]
        artifact = agreement_artifact(units)
        self.assertEqual(artifact["artifact_type"], "annotation_agreement")
        self.assertIn("cohen_kappa", artifact)
        self.assertIn("krippendorff_alpha", artifact)
        claim = PrecisionClaim(
            metric="macro_precision",
            value=0.91,
            corpus_id="customer-1",
            corpus_kind="customer",
            adjudicators=2,
            date="2026-07-25",
            held_out_split=True,
            fn_tracked=True,
        )
        publishable = precision_claim_publishable_with_agreement(
            claim, agreement=artifact, require_agreement=True
        )
        self.assertEqual(
            publishable,
            bool(artifact["pass_threshold_0_60"]) and bool(artifact["pass_alpha_0_67"]),
        )

    def test_low_agreement_blocks_gate(self) -> None:
        # Systematic disagreement drives kappa/alpha below thresholds.
        units = [
            {"ann1": "TP", "ann2": "FP"},
            {"ann1": "FP", "ann2": "TP"},
            {"ann1": "TP", "ann2": "FP"},
            {"ann1": "FP", "ann2": "TP"},
        ]
        artifact = agreement_artifact(units)
        self.assertFalse(artifact["pass_alpha_0_67"])
        self.assertFalse(artifact["pass_threshold_0_60"])


class ExtractionArtifactUncertaintyTests(unittest.TestCase):
    def test_cli_artifact_carries_ci_block(self) -> None:
        from pathlib import Path

        from aerobim.tools.evaluate_extraction import _default_manifest_path, _evaluate_manifest

        manifest = _default_manifest_path()
        if not Path(manifest).is_file():
            self.skipTest("ground-truth manifest missing")
        payload = _evaluate_manifest(manifest, bootstrap_replicates=100, bootstrap_seed=1)
        uncertainty = payload["uncertainty"]
        assert isinstance(uncertainty, dict)
        self.assertEqual(uncertainty["method"], "cluster_percentile_bootstrap")
        cis = uncertainty["confidence_intervals"]
        assert isinstance(cis, dict)
        self.assertIn("macro_f1", cis)
        macro_ci = cis["macro_f1"]
        assert isinstance(macro_ci, dict)
        self.assertLessEqual(macro_ci["lower"], macro_ci["point"])
        self.assertGreaterEqual(macro_ci["upper"], macro_ci["point"])
        self.assertIn("never customer accuracy", str(uncertainty["claim_boundary"]))


class EnglishExtractionGateTests(unittest.TestCase):
    def test_english_manifest_meets_fixture_macro_f1_gate(self) -> None:
        from pathlib import Path

        from aerobim.tools.evaluate_extraction import _evaluate_manifest

        manifest = (
            Path(__file__).resolve().parents[2]
            / "samples"
            / "benchmarks"
            / "english-aec-ground-truth.json"
        )
        if not manifest.is_file():
            self.skipTest("English extraction manifest missing")
        payload = _evaluate_manifest(manifest, bootstrap_replicates=100, bootstrap_seed=1)
        self.assertGreaterEqual(payload["macro_f1"], 0.70)
        self.assertIn("never customer accuracy", str(payload["uncertainty"]["claim_boundary"]))


if __name__ == "__main__":
    unittest.main()
