"""Compare two extraction-quality artifacts with paired significance testing.

Takes two ``extraction_quality_report`` JSONs (same ground-truth manifest,
e.g. before/after an extractor upgrade), aligns fixtures by ``fixture_id``,
and reports: metric deltas, a two-sided paired sign-flip permutation p-value
(exact for n<=12; Monte-Carlo with add-one estimator otherwise), a paired
cluster-bootstrap CI of the difference, Holm-adjusted p-values across the
metric family, and (opt-in) a TOST equivalence verdict against a
pre-specified margin.

Anchors (Jul 2026): Dror et al. 2018; Zmigrod et al. 2022 (exact paired
permutation); Phipson & Smyth 2010 (never-zero p); statsforevals protocol;
arXiv 2511.06701 (harness-enforced statistical rigor); Holm 1979 + Dror et
al. 2017 TACL (multiple comparisons); Schuirmann 1987 / Berger & Hsu 1996 /
Lakens 2017 (TOST, SESOI margin). Claim boundary: verdicts describe the
fixture corpus only — never customer accuracy (RT-001).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from aerobim.domain.eval_statistics import (
    FixtureCounts,
    equivalence_tost,
    holm_bonferroni,
    paired_bootstrap_diff_ci,
    paired_permutation_test,
)

_METRICS = ("macro_f1", "micro_f1", "macro_precision", "macro_recall")
_MAX_INPUT_BYTES = 10 * 1024 * 1024


def _load_fixture_counts(path: Path) -> dict[str, FixtureCounts]:
    if path.stat().st_size > _MAX_INPUT_BYTES:
        raise ValueError(f"{path}: artifact exceeds {_MAX_INPUT_BYTES} bytes")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("artifact_type") != "extraction_quality_report":
        raise ValueError(f"{path}: not an extraction_quality_report artifact")
    counts: dict[str, FixtureCounts] = {}
    for fixture in payload.get("fixtures") or []:
        fixture_id = str(fixture["fixture_id"])
        if fixture_id in counts:
            # RT-C: silent last-wins would let a corrupted artifact drop rows.
            raise ValueError(f"{path}: duplicate fixture_id {fixture_id!r}")
        tp = int(fixture["true_positives"])
        fp = int(fixture["false_positives"])
        fn = int(fixture["false_negatives"])
        if tp < 0 or fp < 0 or fn < 0:
            raise ValueError(f"{path}: negative confusion count for {fixture_id!r}")
        counts[fixture_id] = FixtureCounts(
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
        )
    if not counts:
        raise ValueError(f"{path}: artifact contains no fixtures")
    return counts


def compare_extraction_runs(
    baseline_path: Path,
    candidate_path: Path,
    *,
    replicates: int = 10000,
    bootstrap_replicates: int = 1000,
    seed: int = 20260725,
    significance_alpha: float = 0.05,
    equivalence_margin: float | None = None,
) -> dict[str, Any]:
    """Aligned paired comparison: candidate − baseline per metric."""

    baseline = _load_fixture_counts(baseline_path)
    candidate = _load_fixture_counts(candidate_path)
    shared_ids = sorted(set(baseline) & set(candidate))
    if not shared_ids:
        raise ValueError("no shared fixture_ids between the two artifacts")
    only_baseline = sorted(set(baseline) - set(candidate))
    only_candidate = sorted(set(candidate) - set(baseline))

    aligned_a = [baseline[fixture_id] for fixture_id in shared_ids]
    aligned_b = [candidate[fixture_id] for fixture_id in shared_ids]

    comparisons: dict[str, Any] = {}
    raw_p_values: dict[str, float] = {}
    for metric in _METRICS:
        test = paired_permutation_test(
            aligned_a,
            aligned_b,
            metric=metric,
            replicates=replicates,
            seed=seed,
        )
        diff_ci = paired_bootstrap_diff_ci(
            aligned_a,
            aligned_b,
            metric=metric,
            replicates=bootstrap_replicates,
            seed=seed,
        )
        raw_p_values[metric] = test.p_value
        comparisons[metric] = {
            "permutation_test": test.as_dict(),
            "diff_ci": diff_ci.as_dict(),
            "significant": test.p_value < significance_alpha,
        }
        if equivalence_margin is not None:
            tost = equivalence_tost(
                aligned_a,
                aligned_b,
                metric=metric,
                margin=equivalence_margin,
                replicates=bootstrap_replicates,
                alpha=significance_alpha,
                seed=seed,
            )
            comparisons[metric]["equivalence"] = tost.as_dict()

    # Family-wise correction (Holm 1979) over the four reported metrics;
    # macro_f1 stays the single pre-registered primary endpoint for the
    # regression gate — Holm verdicts qualify the descriptive secondaries.
    family = holm_bonferroni(raw_p_values, alpha=significance_alpha)
    for metric in _METRICS:
        comparisons[metric]["holm_adjusted_p"] = round(family.adjusted_p[metric], 6)
        comparisons[metric]["significant_after_holm"] = family.reject[metric]

    return {
        "artifact_type": "extraction_paired_comparison",
        "schema_version": "1.1.0",
        "baseline": str(baseline_path),
        "candidate": str(candidate_path),
        "n_pairs": len(shared_ids),
        "unaligned_fixtures": {
            "baseline_only": only_baseline,
            "candidate_only": only_candidate,
        },
        "significance_alpha": significance_alpha,
        "multiple_comparisons": {
            "method": family.method,
            "family_size": family.family_size,
            "primary_metric": "macro_f1",
        },
        "equivalence_margin": equivalence_margin,
        "comparisons": comparisons,
        "claim_boundary": (
            "paired verdicts describe the shared fixture corpus only; "
            "never customer accuracy (RT-001); non-significant != equivalent "
            "unless the TOST verdict says so at the pre-specified margin"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--replicates", type=int, default=10000)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260725)
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help=("Exit 1 when macro_f1 significantly decreased (p < alpha and observed_diff < 0)"),
    )
    parser.add_argument(
        "--equivalence-margin",
        type=float,
        default=None,
        help=(
            "Pre-specified SESOI margin for the TOST equivalence verdict "
            "(e.g. 0.02 macro-F1 points); no default on purpose"
        ),
    )
    parser.add_argument(
        "--fail-on-nonequivalence",
        action="store_true",
        help=(
            "Exit 1 unless macro_f1 TOST declares equivalence within "
            "--equivalence-margin (refactoring-safety gate)"
        ),
    )
    args = parser.parse_args(argv)
    if args.fail_on_nonequivalence and args.equivalence_margin is None:
        parser.error("--fail-on-nonequivalence requires --equivalence-margin")
    result = compare_extraction_runs(
        args.baseline.resolve(),
        args.candidate.resolve(),
        replicates=args.replicates,
        bootstrap_replicates=args.bootstrap,
        seed=args.seed,
        equivalence_margin=args.equivalence_margin,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.fail_on_regression:
        macro = result["comparisons"]["macro_f1"]
        if macro["significant"] and macro["permutation_test"]["observed_diff"] < 0:
            print("Significant macro_f1 regression detected.", file=sys.stderr)
            return 1
    if args.fail_on_nonequivalence:
        tost = result["comparisons"]["macro_f1"]["equivalence"]
        if not tost["equivalent"]:
            print(
                "macro_f1 equivalence NOT established at margin "
                f"{args.equivalence_margin} (TOST p={tost['p_tost']}, "
                f"CI [{tost['ci_lower']}, {tost['ci_upper']}], "
                f"stable={tost['stable']}).",
                file=sys.stderr,
            )
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
