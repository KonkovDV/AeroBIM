"""Metamorphic invariants across the statistical ladder (Waves K-R).

Metamorphic testing (Chen et al. 1998; Segura et al. survey; Peng et al.
ESEM 2021 on scientific software) probes the *relations between* inputs and
outputs where no oracle exists for a single point: apply a transformation
whose effect on the result is known a priori and assert the relation. This
suite pins cross-cutting seams of the eval-statistics toolchain that
point-value tests cannot see. All randomness is seeded. Claim boundary:
fixture-corpus mathematics only (RT-001).
"""

from __future__ import annotations

import itertools
import random
import unittest

from aerobim.domain.eval_statistics import (
    FixtureCounts,
    cluster_bootstrap_cis,
    equivalence_tost,
    holm_bonferroni,
    paired_permutation_test,
    paired_scalar_permutation_test,
)
from aerobim.domain.ranking_quality import RankedItem, tie_aware_ndcg
from aerobim.domain.sequential_inference import (
    calibrate_p_to_e,
    calibrate_p_to_e_mixture,
)
from aerobim.domain.study_design import binomial_power_one_sided, wilson_interval

_RNG = random.Random(20260726)
_MIXED_A = [
    FixtureCounts(_RNG.randrange(0, 5), _RNG.randrange(0, 3), _RNG.randrange(0, 3))
    for _ in range(8)
]
_MIXED_B = [
    FixtureCounts(_RNG.randrange(0, 5), _RNG.randrange(0, 3), _RNG.randrange(0, 3))
    for _ in range(8)
]


class NdcgMetamorphicTests(unittest.TestCase):
    def test_invariant_under_strictly_monotone_score_transform(self) -> None:
        """nDCG depends only on the score *ordering* (ties included), so any
        strictly increasing transform (here 2x + 5) must leave it unchanged."""
        items = [
            RankedItem("a", 30, 2),
            RankedItem("b", 30, 0),  # tie preserved by affine map
            RankedItem("c", 20, 1),
            RankedItem("d", 10, 2),
        ]
        transformed = [
            RankedItem(item.item_id, 2 * item.score + 5, item.relevance) for item in items
        ]
        self.assertEqual(
            tie_aware_ndcg(items).as_dict()["ndcg"],
            tie_aware_ndcg(transformed).as_dict()["ndcg"],
        )


class PermutationMetamorphicTests(unittest.TestCase):
    def test_paired_test_invariant_under_joint_pair_shuffle(self) -> None:
        """Pairs are exchangeable units: shuffling both lists with the same
        permutation must not change the exact p-value or observed diff."""
        order = list(range(len(_MIXED_A)))
        random.Random(5).shuffle(order)
        shuffled_a = [_MIXED_A[i] for i in order]
        shuffled_b = [_MIXED_B[i] for i in order]
        base = paired_permutation_test(_MIXED_A, _MIXED_B)
        moved = paired_permutation_test(shuffled_a, shuffled_b)
        self.assertEqual(base.p_value, moved.p_value)
        self.assertAlmostEqual(base.observed_diff, moved.observed_diff, places=12)

    def test_scalar_test_invariant_under_common_shift(self) -> None:
        """Adding the same constant to both sides leaves all per-pair diffs
        unchanged, hence the identical exact p-value."""
        values_a = [0.1, 0.5, 0.4, 0.9, 0.3, 0.7]
        values_b = [0.2, 0.4, 0.6, 0.8, 0.2, 0.9]
        base = paired_scalar_permutation_test(values_a, values_b)
        shifted = paired_scalar_permutation_test(
            [v + 0.05 for v in values_a], [v + 0.05 for v in values_b]
        )
        self.assertEqual(base.p_value, shifted.p_value)
        self.assertAlmostEqual(base.observed_diff, shifted.observed_diff, places=12)


class WilsonBinomialMetamorphicTests(unittest.TestCase):
    def test_wilson_success_failure_symmetry(self) -> None:
        """Relabeling successes as failures mirrors the interval:
        lower(k, n) == 1 - upper(n-k, n) for all k."""
        n = 17
        for k in range(n + 1):
            direct = wilson_interval(k, n)
            mirrored = wilson_interval(n - k, n)
            self.assertAlmostEqual(direct.lower, 1.0 - mirrored.upper, places=12, msg=str(k))

    def test_exact_binomial_size_and_power_monotonicity(self) -> None:
        """Attained alpha never exceeds nominal alpha (conservative critical
        value), and power is strictly increasing in the true p."""
        for n in (10, 20, 35):
            for p0 in (0.5, 0.6):
                powers = []
                for p_true in (0.7, 0.8, 0.9):
                    design = binomial_power_one_sided(n=n, p0=p0, p_true=p_true)
                    self.assertLessEqual(design.attained_alpha, design.alpha + 1e-12)
                    powers.append(design.power)
                self.assertEqual(powers, sorted(powers), msg=f"n={n} p0={p0}")


class HolmTostMetamorphicTests(unittest.TestCase):
    def test_holm_adjusted_never_below_raw_and_order_free(self) -> None:
        family = {"m1": 0.02, "m2": 0.9, "m3": 0.049, "m4": 0.2}
        result = holm_bonferroni(family)
        for name, raw in family.items():
            self.assertGreaterEqual(result.adjusted_p[name] + 1e-15, raw)
        reordered = holm_bonferroni(dict(reversed(list(family.items()))))
        self.assertEqual(result.adjusted_p, reordered.adjusted_p)
        self.assertEqual(result.reject, reordered.reject)

    def test_tost_equivalence_monotone_in_margin(self) -> None:
        """If a corpus certifies equivalence at margin m, any wider margin
        must certify it too (same data, same seed)."""
        margins = (0.2, 0.4, 0.8)
        verdicts = [
            equivalence_tost(_MIXED_A, _MIXED_A, margin=margin, replicates=300, seed=9).equivalent
            for margin in margins
        ]
        self.assertTrue(verdicts[0])  # identical systems, generous margins
        for narrow, wide in itertools.pairwise(verdicts):
            self.assertLessEqual(int(narrow), int(wide))


class CalibratorBootstrapMetamorphicTests(unittest.TestCase):
    def test_calibrators_monotone_decreasing_in_p(self) -> None:
        grid = [i / 40 for i in range(1, 40)]
        for calibrator in (calibrate_p_to_e, calibrate_p_to_e_mixture):
            values = [calibrator(p) for p in grid]
            for left, right in itertools.pairwise(values):
                self.assertGreaterEqual(left + 1e-15, right, msg=calibrator.__name__)

    def test_point_metrics_invariant_under_cluster_duplication(self) -> None:
        """Duplicating every cluster changes nothing about the point micro/
        macro metrics (sums and means scale together)."""
        base = cluster_bootstrap_cis(_MIXED_A, replicates=50, seed=1)
        doubled = cluster_bootstrap_cis([*_MIXED_A, *_MIXED_A], replicates=50, seed=1)
        for metric in base:
            self.assertAlmostEqual(base[metric].point, doubled[metric].point, places=12, msg=metric)


if __name__ == "__main__":
    unittest.main()
