"""A/B comparison of two ranker profiles via paired tie-aware nDCG.

Closes the Wave N deferred item: AeroBIM ships two real priority rankers
(``compute_issue_priority`` profiles ``default`` and ``samolet``), so the
paired comparison is now wired. Input: two ``ranking_quality_labels``
artifacts over the *same* cases/findings/relevance grades, differing only
in ``priority_score`` (profile A vs profile B).

Method (Jul 2026 anchors): per-case tie-aware expected nDCG (McSherry &
Najork 2008; Wave N) becomes the per-cluster scalar; then Wave L/M
machinery applies — paired sign-flip permutation on per-case nDCG (exact
n<=12, add-one MC otherwise), paired bootstrap CI of the mean difference,
Holm correction across the reported cutoffs, and Miller 2024 (arXiv
2411.00640) motivates the paired design itself: pairing strips shared
case difficulty out of the comparison variance.

Claim boundary: fixture rankings never demonstrate customer ranking
quality (RT-001); ranker choice is advisory ordering only and never
affects ``summary.passed``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from aerobim.domain.eval_statistics import (
    holm_bonferroni,
    paired_scalar_bootstrap_diff_ci,
    paired_scalar_permutation_test,
)
from aerobim.domain.ranking_quality import RankedItem, tie_aware_ndcg
from aerobim.tools.evaluate_ranking_quality import _parse_cases

_DEFAULT_CUTOFFS = (5, 10)
_MAX_INPUT_BYTES = 10 * 1024 * 1024


def _load_cases(path: Path) -> tuple[str, dict[str, list[RankedItem]]]:
    if path.stat().st_size > _MAX_INPUT_BYTES:
        raise ValueError(f"{path}: artifact exceeds {_MAX_INPUT_BYTES} bytes")
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = _parse_cases(payload, path)
    return str(payload["dataset_status"]), {case_id: items for case_id, items in cases}


def _assert_same_universe(
    cases_a: dict[str, list[RankedItem]],
    cases_b: dict[str, list[RankedItem]],
) -> list[str]:
    """Profiles must rank the same findings with the same grades."""

    if set(cases_a) != set(cases_b):
        only_a = sorted(set(cases_a) - set(cases_b))
        only_b = sorted(set(cases_b) - set(cases_a))
        raise ValueError(f"case sets differ: only_a={only_a}, only_b={only_b}")
    for case_id in cases_a:
        grades_a = {item.item_id: item.relevance for item in cases_a[case_id]}
        grades_b = {item.item_id: item.relevance for item in cases_b[case_id]}
        if grades_a != grades_b:
            raise ValueError(
                f"case {case_id!r}: finding ids or relevance grades differ "
                "between profiles — only priority_score may vary"
            )
    return sorted(cases_a)


def compare_ranker_profiles(
    profile_a_path: Path,
    profile_b_path: Path,
    *,
    cutoffs: tuple[int, ...] = _DEFAULT_CUTOFFS,
    gain: str = "exponential",
    replicates: int = 10000,
    bootstrap_replicates: int = 1000,
    seed: int = 20260726,
    significance_alpha: float = 0.05,
) -> dict[str, Any]:
    """Paired per-case nDCG comparison: profile B − profile A."""

    if len(set(cutoffs)) != len(cutoffs) or any(k <= 0 for k in cutoffs):
        raise ValueError("cutoffs must be unique positive integers")
    status_a, cases_a = _load_cases(profile_a_path)
    status_b, cases_b = _load_cases(profile_b_path)
    case_ids = _assert_same_universe(cases_a, cases_b)

    cutoff_keys: list[tuple[str, int | None]] = [(f"ndcg_at_{k}", k) for k in cutoffs]
    cutoff_keys.append(("ndcg_full", None))

    # Per-case nDCG per profile; undefined cases (IDCG=0) are excluded from
    # the paired sample — identical exclusion on both sides by construction
    # (grades are identical), so pairing stays aligned.
    aligned: dict[str, tuple[list[float], list[float]]] = {key: ([], []) for key, _ in cutoff_keys}
    undefined_case_ids: list[str] = []
    for case_id in case_ids:
        full_a = tie_aware_ndcg(cases_a[case_id], k=None, gain=gain)
        if not full_a.defined:
            undefined_case_ids.append(case_id)
            continue
        for key, k in cutoff_keys:
            aligned[key][0].append(tie_aware_ndcg(cases_a[case_id], k=k, gain=gain).ndcg)
            aligned[key][1].append(tie_aware_ndcg(cases_b[case_id], k=k, gain=gain).ndcg)

    if not aligned["ndcg_full"][0]:
        raise ValueError("no defined cases shared by both profiles")

    comparisons: dict[str, Any] = {}
    raw_p_values: dict[str, float] = {}
    for key, _ in cutoff_keys:
        values_a, values_b = aligned[key]
        test = paired_scalar_permutation_test(
            values_a,
            values_b,
            metric=key,
            replicates=replicates,
            seed=seed,
        )
        diff_ci = paired_scalar_bootstrap_diff_ci(
            values_a,
            values_b,
            metric=key,
            replicates=bootstrap_replicates,
            seed=seed,
        )
        raw_p_values[key] = test.p_value
        comparisons[key] = {
            "mean_ndcg_a": round(sum(values_a) / len(values_a), 6),
            "mean_ndcg_b": round(sum(values_b) / len(values_b), 6),
            "permutation_test": test.as_dict(),
            "diff_ci": diff_ci.as_dict(),
            "significant": test.p_value < significance_alpha,
        }

    family = holm_bonferroni(raw_p_values, alpha=significance_alpha)
    for key, _ in cutoff_keys:
        comparisons[key]["holm_adjusted_p"] = round(family.adjusted_p[key], 6)
        comparisons[key]["significant_after_holm"] = family.reject[key]

    return {
        "artifact_type": "ranker_profile_comparison",
        "schema_version": "1.0.0",
        "profile_a": str(profile_a_path),
        "profile_b": str(profile_b_path),
        "dataset_status": {"a": status_a, "b": status_b},
        "gain": gain,
        "n_cases": len(case_ids),
        "n_defined_pairs": len(aligned["ndcg_full"][0]),
        "undefined_case_ids": undefined_case_ids,
        "significance_alpha": significance_alpha,
        "multiple_comparisons": {
            "method": family.method,
            "family_size": family.family_size,
            "primary_metric": "ndcg_full",
        },
        "comparisons": comparisons,
        "claim_boundary": (
            "paired per-case nDCG on the labeled corpus only; fixture "
            "rankings never demonstrate customer ranking quality (RT-001); "
            "ranker choice never affects summary.passed"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile-a", type=Path, required=True)
    parser.add_argument("--profile-b", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--cutoffs", type=int, nargs="+", default=list(_DEFAULT_CUTOFFS))
    parser.add_argument("--gain", choices=("exponential", "linear"), default="exponential")
    parser.add_argument("--replicates", type=int, default=10000)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260726)
    args = parser.parse_args(argv)
    report = compare_ranker_profiles(
        args.profile_a.resolve(),
        args.profile_b.resolve(),
        cutoffs=tuple(args.cutoffs),
        gain=args.gain,
        replicates=args.replicates,
        bootstrap_replicates=args.bootstrap,
        seed=args.seed,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
