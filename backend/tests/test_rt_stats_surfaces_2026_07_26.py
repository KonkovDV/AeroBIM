"""Red Team regression kills for Waves K-O statistical surfaces (2026-07-26).

Each test pins one confirmed runtime finding from the RT audit; if a fix
regresses, the corresponding exploit becomes reproducible again.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.eval_statistics import (
    FixtureCounts,
    cluster_bootstrap_cis,
    equivalence_tost,
    paired_bootstrap_diff_ci,
    paired_permutation_test,
    scalar_cluster_bootstrap_ci,
)
from aerobim.domain.ranking_quality import RankedItem, tie_aware_ndcg
from aerobim.domain.sequential_inference import new_e_process_state, update_e_process
from aerobim.tools.compare_extraction_runs import _load_fixture_counts
from aerobim.tools.evaluate_ranking_quality import evaluate_ranking_quality
from aerobim.tools.sequential_regression_monitor import _state_from_dict

_WORSE = FixtureCounts(true_positives=1, false_positives=1, false_negatives=0)
_BETTER = FixtureCounts(true_positives=1, false_positives=0, false_negatives=0)


class RtAZeroReplicateCertificates(unittest.TestCase):
    """RT-A: replicates=0 produced a degenerate [0,0] CI and a free
    equivalence certificate for a 0.33 shift against a 0.05 margin."""

    def test_tost_rejects_zero_replicates(self) -> None:
        with self.assertRaises(ValueError):
            equivalence_tost([_WORSE] * 8, [_BETTER] * 8, margin=0.05, replicates=0)

    def test_all_bootstrap_paths_reject_zero_replicates(self) -> None:
        with self.assertRaises(ValueError):
            scalar_cluster_bootstrap_ci([0.9] * 6, metric="m", replicates=0)
        with self.assertRaises(ValueError):
            cluster_bootstrap_cis([_WORSE] * 6, replicates=0)
        with self.assertRaises(ValueError):
            paired_bootstrap_diff_ci([_WORSE] * 6, [_BETTER] * 6, replicates=0)
        with self.assertRaises(ValueError):
            paired_permutation_test([_WORSE] * 13, [_BETTER] * 13, replicates=0)


class RtBNanRankingScores(unittest.TestCase):
    """RT-B: json.loads accepts NaN; NaN scores broke sorting and tie-group
    equality, making nDCG input-order dependent (0.964 vs 0.689)."""

    def test_nan_and_inf_scores_rejected(self) -> None:
        with self.assertRaises(ValueError):
            tie_aware_ndcg([RankedItem("a", float("nan"), 2)])
        with self.assertRaises(ValueError):
            tie_aware_ndcg([RankedItem("a", float("inf"), 2)])

    def test_nan_score_in_labels_artifact_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            labels = Path(tmp) / "labels.json"
            labels.write_text(
                '{"artifact_type": "ranking_quality_labels", "dataset_status": "draft",'
                ' "cases": [{"case_id": "c", "findings":'
                ' [{"finding_id": "f", "priority_score": NaN, "relevance": 2}]}]}',
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                evaluate_ranking_quality(labels)


class RtCArtifactLoaderHardening(unittest.TestCase):
    """RT-C: negative confusion counts and duplicate fixture_ids were
    silently accepted (last-wins) by the shared comparison loader."""

    def _write(self, path: Path, fixtures: list[dict[str, object]]) -> None:
        path.write_text(
            json.dumps({"artifact_type": "extraction_quality_report", "fixtures": fixtures}),
            encoding="utf-8",
        )

    def test_negative_counts_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.json"
            self._write(
                path,
                [
                    {
                        "fixture_id": "f1",
                        "true_positives": -5,
                        "false_positives": 0,
                        "false_negatives": 0,
                    }
                ],
            )
            with self.assertRaises(ValueError):
                _load_fixture_counts(path)

    def test_duplicate_fixture_ids_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.json"
            row = {
                "fixture_id": "f1",
                "true_positives": 1,
                "false_positives": 0,
                "false_negatives": 0,
            }
            self._write(path, [row, dict(row)])
            with self.assertRaises(ValueError):
                _load_fixture_counts(path)


class RtDFullPrecisionPersistence(unittest.TestCase):
    """RT-D: wealth was persisted rounded to 6 dp — martingale drift across
    CLI restarts. The state dict must round-trip bit-exact."""

    def test_wealth_round_trips_exactly(self) -> None:
        state = new_e_process_state(alpha=0.05, calibrator="power", kappa=0.5)
        state = update_e_process(state, run_id="r", p_value=0.0123)
        payload = state.as_dict()
        self.assertEqual(payload["wealth"], state.wealth)
        self.assertEqual(payload["history"][0]["e_value"], state.history[0].e_value)
        restored = _state_from_dict(json.loads(json.dumps(payload)))
        self.assertEqual(restored.wealth, state.wealth)


class RtETamperedStateRejected(unittest.TestCase):
    """RT-E: a tampered state (alpha=0.999999 → Ville threshold ≈1, or an
    unknown calibrator) was accepted on reload without validation."""

    def _payload(self, **overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "artifact_type": "sequential_regression_monitor",
            "alpha": 0.05,
            "calibrator": "power",
            "kappa": 0.5,
            "wealth": 1.0,
            "rejected": False,
            "history": [],
        }
        payload.update(overrides)
        return payload

    def test_out_of_range_alpha_rejected(self) -> None:
        with self.assertRaises(ValueError):
            _state_from_dict(self._payload(alpha=1.5))

    def test_unknown_calibrator_rejected(self) -> None:
        with self.assertRaises(ValueError):
            _state_from_dict(self._payload(calibrator="bogus"))

    def test_nonpositive_or_nonfinite_wealth_rejected(self) -> None:
        with self.assertRaises(ValueError):
            _state_from_dict(self._payload(wealth=0.0))
        with self.assertRaises(ValueError):
            _state_from_dict(self._payload(wealth=float("inf")))

    def test_valid_state_still_loads(self) -> None:
        state = _state_from_dict(self._payload())
        self.assertEqual(state.alpha, 0.05)
        self.assertEqual(state.threshold, 20.0)


class RtFCutoffValidation(unittest.TestCase):
    """RT hardening: duplicate or non-positive cutoffs silently collapsed
    summary keys in the ranking report."""

    def test_duplicate_and_nonpositive_cutoffs_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            labels = Path(tmp) / "labels.json"
            labels.write_text(
                json.dumps(
                    {
                        "artifact_type": "ranking_quality_labels",
                        "dataset_status": "draft",
                        "cases": [
                            {
                                "case_id": "c",
                                "findings": [
                                    {
                                        "finding_id": "f",
                                        "priority_score": 1,
                                        "relevance": 2,
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                evaluate_ranking_quality(labels, cutoffs=(5, 5))
            with self.assertRaises(ValueError):
                evaluate_ranking_quality(labels, cutoffs=(0,))


if __name__ == "__main__":
    unittest.main()
