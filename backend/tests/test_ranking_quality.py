"""Tie-aware nDCG ranking quality (Wave N, Jul 2026).

Anchors: Jarvelin & Kekalainen 2002 (nDCG, log discount); Wang et al. 2013
(COLT, discount consistency); McSherry & Najork 2008 (tie-aware expected
metrics); Burges 2005 / LETOR (exponential gain); Fuhr 2018 (metric
pitfalls). Claim boundary: fixture rankings never demonstrate customer
ranking quality (RT-001); nDCG never affects summary.passed.
"""

from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.eval_statistics import scalar_cluster_bootstrap_ci
from aerobim.domain.ranking_quality import RankedItem, tie_aware_ndcg
from aerobim.tools.evaluate_ranking_quality import evaluate_ranking_quality, main

_D2 = 1.0  # discount at position 1 = 1/log2(2)
_D3 = 1.0 / math.log2(3.0)  # discount at position 2
_D4 = 0.5  # discount at position 3 = 1/log2(4)


def _item(item_id: str, score: float, relevance: int) -> RankedItem:
    return RankedItem(item_id=item_id, score=score, relevance=relevance)


class TieAwareNdcgTests(unittest.TestCase):
    def test_perfect_order_no_ties_is_one(self) -> None:
        items = [_item("a", 30, 2), _item("b", 20, 1), _item("c", 10, 0)]
        result = tie_aware_ndcg(items)
        self.assertTrue(result.defined)
        self.assertEqual(result.tie_group_count, 3)
        self.assertAlmostEqual(result.ndcg, 1.0, places=12)

    def test_worst_order_hand_computed(self) -> None:
        """rel (0,1,2) ranked by descending score: DCG = 0·1 + 1·d3 + 3·d4;
        IDCG = 3·1 + 1·d3 (exp gains 3,1,0) — written out by hand."""
        items = [_item("a", 30, 0), _item("b", 20, 1), _item("c", 10, 2)]
        result = tie_aware_ndcg(items)
        expected_dcg = 0.0 * _D2 + 1.0 * _D3 + 3.0 * _D4
        expected_idcg = 3.0 * _D2 + 1.0 * _D3 + 0.0 * _D4
        self.assertAlmostEqual(result.dcg, expected_dcg, places=12)
        self.assertAlmostEqual(result.idcg, expected_idcg, places=12)
        self.assertAlmostEqual(result.ndcg, expected_dcg / expected_idcg, places=12)

    def test_full_tie_matches_enumerated_permutations(self) -> None:
        """Two tied items rel (2,0): orderings give DCG 3·1 and 3·d3; the
        closed form must equal their mean (McSherry–Najork expectation)."""
        items = [_item("a", 10, 2), _item("b", 10, 0)]
        result = tie_aware_ndcg(items)
        enumerated_mean = (3.0 * _D2 + 3.0 * _D3) / 2
        self.assertEqual(result.tie_group_count, 1)
        self.assertAlmostEqual(result.dcg, enumerated_mean, places=12)
        self.assertAlmostEqual(result.ndcg, enumerated_mean / 3.0, places=12)

    def test_cutoff_straddling_tie_group(self) -> None:
        """Same tied pair at k=1: orderings give DCG@1 of 3 and 0, so the
        expectation is 1.5; IDCG@1 = 3 => nDCG@1 = 0.5 exactly."""
        items = [_item("a", 10, 2), _item("b", 10, 0)]
        result = tie_aware_ndcg(items, k=1)
        self.assertAlmostEqual(result.dcg, 1.5, places=12)
        self.assertAlmostEqual(result.idcg, 3.0, places=12)
        self.assertEqual(result.ndcg, 0.5)

    def test_input_order_invariance_under_ties(self) -> None:
        forward = [_item("a", 10, 2), _item("b", 10, 0), _item("c", 5, 1)]
        shuffled = [forward[1], forward[2], forward[0]]
        self.assertEqual(
            tie_aware_ndcg(forward).as_dict(),
            tie_aware_ndcg(shuffled).as_dict(),
        )

    def test_all_irrelevant_case_is_undefined_not_zero_or_one(self) -> None:
        result = tie_aware_ndcg([_item("a", 10, 0), _item("b", 5, 0)])
        self.assertFalse(result.defined)
        self.assertEqual(result.idcg, 0.0)

    def test_linear_vs_exponential_gain(self) -> None:
        items = [_item("a", 10, 2)]
        self.assertAlmostEqual(tie_aware_ndcg(items, gain="linear").dcg, 2.0, places=12)
        self.assertAlmostEqual(tie_aware_ndcg(items, gain="exponential").dcg, 3.0, places=12)

    def test_invalid_inputs_rejected(self) -> None:
        with self.assertRaises(ValueError):
            tie_aware_ndcg([])
        with self.assertRaises(ValueError):
            tie_aware_ndcg([_item("a", 1, 1)], k=0)
        with self.assertRaises(ValueError):
            tie_aware_ndcg([_item("a", 1, -1)])
        with self.assertRaises(ValueError):
            tie_aware_ndcg([_item("a", 1, 1)], gain="bogus")


class ScalarBootstrapTests(unittest.TestCase):
    def test_identical_clusters_degenerate_ci(self) -> None:
        ci = scalar_cluster_bootstrap_ci([0.8] * 6, metric="mean_ndcg_full", replicates=200)
        self.assertAlmostEqual(ci.point, 0.8, places=12)
        self.assertAlmostEqual(ci.lower, 0.8, places=12)
        self.assertAlmostEqual(ci.upper, 0.8, places=12)
        self.assertTrue(ci.stable)

    def test_small_cluster_count_flagged_unstable(self) -> None:
        ci = scalar_cluster_bootstrap_ci([0.1, 0.9], metric="mean_ndcg_full", replicates=100)
        self.assertFalse(ci.stable)

    def test_empty_rejected(self) -> None:
        with self.assertRaises(ValueError):
            scalar_cluster_bootstrap_ci([], metric="mean_ndcg_full")


def _labels_artifact(path: Path, *, status: str, cases: list[dict[str, object]]) -> None:
    payload = {
        "artifact_type": "ranking_quality_labels",
        "schema_version": "1.0.0",
        "dataset_id": "rq-fixture",
        "dataset_status": status,
        "cases": cases,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _case(case_id: str, rows: list[tuple[str, float, int]]) -> dict[str, object]:
    return {
        "case_id": case_id,
        "findings": [
            {"finding_id": fid, "priority_score": score, "relevance": rel}
            for fid, score, rel in rows
        ],
    }


class EvaluateRankingQualityCliTests(unittest.TestCase):
    def test_report_shape_and_fixture_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            labels = Path(tmp) / "labels.json"
            cases = [
                _case(f"case-{i}", [("f1", 30, 2), ("f2", 20, 1), ("f3", 10, 0)]) for i in range(6)
            ]
            _labels_artifact(labels, status="draft", cases=cases)
            report = evaluate_ranking_quality(labels)
        self.assertEqual(report["artifact_type"], "ranking_quality_report")
        self.assertEqual(report["case_count"], 6)
        self.assertEqual(report["defined_case_count"], 6)
        summary = report["summary"]
        self.assertAlmostEqual(summary["ndcg_full"]["point"], 1.0, places=12)
        self.assertTrue(summary["ndcg_full"]["stable"])
        self.assertIn("must not be published", report["warning"])
        self.assertIn("never affects summary.passed", report["claim_boundary"])

    def test_undefined_cases_excluded_and_listed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            labels = Path(tmp) / "labels.json"
            cases = [
                _case("good", [("f1", 30, 2), ("f2", 10, 0)]),
                _case("all-noise", [("f1", 30, 0), ("f2", 10, 0)]),
            ]
            _labels_artifact(labels, status="draft", cases=cases)
            report = evaluate_ranking_quality(labels)
        self.assertEqual(report["defined_case_count"], 1)
        self.assertEqual(report["undefined_case_ids"], ["all-noise"])
        # The perfect single defined case drives the mean; nothing silently 0.
        self.assertAlmostEqual(report["summary"]["ndcg_full"]["point"], 1.0, places=12)

    def test_all_undefined_yields_null_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            labels = Path(tmp) / "labels.json"
            _labels_artifact(
                labels,
                status="draft",
                cases=[_case("noise", [("f1", 30, 0)])],
            )
            report = evaluate_ranking_quality(labels)
        self.assertIsNone(report["summary"]["ndcg_full"])

    def test_duplicate_and_invalid_grades_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            labels = Path(tmp) / "labels.json"
            _labels_artifact(
                labels,
                status="draft",
                cases=[
                    _case("dup", [("f1", 30, 2), ("f1", 20, 1)]),
                ],
            )
            with self.assertRaises(ValueError):
                evaluate_ranking_quality(labels)
            _labels_artifact(
                labels,
                status="draft",
                cases=[_case("bad-grade", [("f1", 30, 3)])],
            )
            with self.assertRaises(ValueError):
                evaluate_ranking_quality(labels)
            _labels_artifact(labels, status="published", cases=[])
            with self.assertRaises(ValueError):
                evaluate_ranking_quality(labels)

    def test_cli_writes_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            labels = Path(tmp) / "labels.json"
            output = Path(tmp) / "out" / "report.json"
            _labels_artifact(
                labels,
                status="draft",
                cases=[_case("c1", [("f1", 30, 2), ("f2", 10, 1)])],
            )
            exit_code = main(["--labels", str(labels), "--output", str(output)])
            self.assertEqual(exit_code, 0)
            written = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(written["artifact_type"], "ranking_quality_report")

    def test_determinism_given_seed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            labels = Path(tmp) / "labels.json"
            cases = [
                _case(f"c{i}", [("f1", 30, 2), ("f2", 20, i % 3), ("f3", 10, 0)]) for i in range(7)
            ]
            _labels_artifact(labels, status="draft", cases=cases)
            first = evaluate_ranking_quality(labels, seed=11)
            second = evaluate_ranking_quality(labels, seed=11)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
