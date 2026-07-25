"""Ranking-quality harness: tie-aware nDCG@k over adjudicated graded labels.

Closes the TZ v2 "nDCG (graded 0/1/2)" harness item (previously *planned*,
see HARNESS_AND_DEMO_RUNBOOK_2026.md). Input is a ranking artifact with one
entry per case: ranked findings carrying the deterministic priority score
and the adjudicated relevance grade (0 = noise/FP, 1 = useful, 2 = critical).

Method (Jul 2026 anchors): tie-aware expected nDCG (McSherry & Najork 2008)
— AeroBIM priorities are integer scores, ties are the norm; exponential
gain 2^rel - 1 (Burges 2005 / LETOR); log2 discount (Jarvelin & Kekalainen
2002; Wang et al. 2013). Mean nDCG over cases gets a cluster-bootstrap
percentile CI (case = cluster, Wave K). All-irrelevant cases (IDCG = 0) are
excluded and counted — never silently scored 0 or 1.

Claim boundary: fixture rankings never demonstrate customer ranking quality
(RT-001); nDCG orders review effort and never affects ``summary.passed``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from aerobim.domain.eval_statistics import scalar_cluster_bootstrap_ci
from aerobim.domain.ranking_quality import NdcgResult, RankedItem, tie_aware_ndcg

_DEFAULT_CUTOFFS = (5, 10)
_DATASET_STATUSES = {"synthetic", "draft", "adjudicated"}
_MAX_GRADE = 2
_MAX_INPUT_BYTES = 10 * 1024 * 1024


def _parse_cases(payload: dict[str, Any], path: Path) -> list[tuple[str, list[RankedItem]]]:
    if payload.get("artifact_type") != "ranking_quality_labels":
        raise ValueError(f"{path}: not a ranking_quality_labels artifact")
    status = str(payload.get("dataset_status", ""))
    if status not in _DATASET_STATUSES:
        raise ValueError(f"{path}: dataset_status must be one of {sorted(_DATASET_STATUSES)}")
    cases: list[tuple[str, list[RankedItem]]] = []
    seen_case_ids: set[str] = set()
    for case in payload.get("cases") or []:
        case_id = str(case["case_id"])
        if case_id in seen_case_ids:
            raise ValueError(f"{path}: duplicate case_id {case_id!r}")
        seen_case_ids.add(case_id)
        items: list[RankedItem] = []
        seen_item_ids: set[str] = set()
        for row in case.get("findings") or []:
            item_id = str(row["finding_id"])
            if item_id in seen_item_ids:
                raise ValueError(f"{path}: duplicate finding_id {item_id!r} in {case_id!r}")
            seen_item_ids.add(item_id)
            relevance = int(row["relevance"])
            if not 0 <= relevance <= _MAX_GRADE:
                raise ValueError(
                    f"{path}: relevance out of 0..{_MAX_GRADE} for {item_id!r}: {relevance}"
                )
            items.append(
                RankedItem(
                    item_id=item_id,
                    score=float(row["priority_score"]),
                    relevance=relevance,
                )
            )
        if items:
            cases.append((case_id, items))
    if not cases:
        raise ValueError(f"{path}: artifact contains no non-empty cases")
    return cases


def evaluate_ranking_quality(
    labels_path: Path,
    *,
    cutoffs: tuple[int, ...] = _DEFAULT_CUTOFFS,
    gain: str = "exponential",
    bootstrap_replicates: int = 1000,
    seed: int = 20260726,
) -> dict[str, Any]:
    """Per-case tie-aware nDCG@k + cluster-bootstrap CI of the mean."""

    if len(set(cutoffs)) != len(cutoffs) or any(k <= 0 for k in cutoffs):
        raise ValueError("cutoffs must be unique positive integers")
    if labels_path.stat().st_size > _MAX_INPUT_BYTES:
        raise ValueError(f"{labels_path}: artifact exceeds {_MAX_INPUT_BYTES} bytes")
    payload = json.loads(labels_path.read_text(encoding="utf-8"))
    cases = _parse_cases(payload, labels_path)
    dataset_status = str(payload["dataset_status"])

    cutoff_keys: list[tuple[str, int | None]] = [(f"ndcg_at_{k}", k) for k in cutoffs]
    cutoff_keys.append(("ndcg_full", None))

    per_case: dict[str, dict[str, Any]] = {}
    defined_values: dict[str, list[float]] = {key: [] for key, _ in cutoff_keys}
    undefined_case_ids: list[str] = []
    for case_id, items in cases:
        case_results: dict[str, NdcgResult] = {
            key: tie_aware_ndcg(items, k=k, gain=gain) for key, k in cutoff_keys
        }
        full = case_results["ndcg_full"]
        if full.defined:
            for key, _ in cutoff_keys:
                defined_values[key].append(case_results[key].ndcg)
        else:
            undefined_case_ids.append(case_id)
        per_case[case_id] = {key: result.as_dict() for key, result in case_results.items()}

    summary: dict[str, Any] = {}
    for key, _ in cutoff_keys:
        values = defined_values[key]
        if values:
            ci = scalar_cluster_bootstrap_ci(
                values,
                metric=f"mean_{key}",
                replicates=bootstrap_replicates,
                seed=seed,
            )
            summary[key] = ci.as_dict()
        else:
            # Fail-closed: no defined cases -> no number at all.
            summary[key] = None

    warning = None
    if dataset_status != "adjudicated":
        warning = (
            "Dataset is not adjudicated customer evidence; ranking metrics are "
            "harness/fixture results and must not be published as AeroBIM "
            "product ranking quality."
        )

    return {
        "artifact_type": "ranking_quality_report",
        "schema_version": "1.0.0",
        "labels": str(labels_path),
        "dataset_id": str(payload.get("dataset_id", "")),
        "dataset_status": dataset_status,
        "gain": gain,
        "case_count": len(cases),
        "defined_case_count": len(cases) - len(undefined_case_ids),
        "undefined_case_ids": sorted(undefined_case_ids),
        "summary": summary,
        "per_case": per_case,
        "warning": warning,
        "claim_boundary": (
            "tie-aware expected nDCG on the labeled corpus only; fixture "
            "rankings never demonstrate customer ranking quality (RT-001); "
            "nDCG never affects summary.passed"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--cutoffs", type=int, nargs="+", default=list(_DEFAULT_CUTOFFS))
    parser.add_argument("--gain", choices=("exponential", "linear"), default="exponential")
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260726)
    args = parser.parse_args(argv)
    report = evaluate_ranking_quality(
        args.labels.resolve(),
        cutoffs=tuple(args.cutoffs),
        gain=args.gain,
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
