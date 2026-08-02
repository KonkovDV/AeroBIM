"""WP-07: Wilson CI + sample-size planner for the quality measurement protocol.

Computes Wilson score intervals for precision (TP/(TP+FP)) and recall
(TP/(TP+FN)) from confusion counts, plus the smallest n whose Wilson
half-width at an expected rate stays within a requested margin.

Reuses ``aerobim.domain.study_design.wilson_interval`` /
``required_n_for_wilson_halfwidth`` (Wilson 1927; Brown–Cai–DasGupta 2001).
Ranking quality (nDCG) remains on ``aerobim.tools.evaluate_ranking_quality``.

Claim boundary: sizes and intervals for an adjudicated pilot protocol only;
never upgrades fixture evidence to customer evidence (RT-001); never claims
>90% product accuracy.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from aerobim.domain.study_design import (
    required_n_for_wilson_halfwidth,
    wilson_interval,
)

CLAIM_BOUNDARY = (
    "Protocol planning / Wilson reporting only. Fixture counts never become "
    "customer precision (RT-001). Never claim >90% product accuracy."
)

INTERIM_CONFIRMED_FINDING_RATE_TARGET = 0.60
"""Interim pilot target: TP/(TP+FP) ≥ 0.60 (MIK / Samolet contract interim)."""


def _confidence_to_alpha(confidence: float) -> float:
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must lie strictly inside (0, 1)")
    return 1.0 - confidence


def wilson_for_rate(
    successes: int,
    trials: int,
    *,
    confidence: float = 0.95,
) -> dict[str, object]:
    if trials <= 0:
        raise ValueError("trials must be positive")
    interval = wilson_interval(successes, trials, alpha=_confidence_to_alpha(confidence))
    return {
        "successes": successes,
        "trials": trials,
        "confidence": confidence,
        **interval.as_dict(),
    }


def compute_precision_recall_wilson(
    *,
    true_positives: int,
    false_positives: int,
    false_negatives: int,
    confidence: float = 0.95,
) -> dict[str, Any]:
    """Wilson CIs for precision and recall from TP/FP/FN counts."""

    for name, value in (
        ("true_positives", true_positives),
        ("false_positives", false_positives),
        ("false_negatives", false_negatives),
    ):
        if value < 0:
            raise ValueError(f"{name} must be non-negative")

    precision_n = true_positives + false_positives
    recall_n = true_positives + false_negatives

    precision_block: dict[str, object]
    if precision_n == 0:
        precision_block = {
            "defined": False,
            "reason": "TP+FP=0 — precision undefined",
            "point": None,
        }
    else:
        precision_block = {
            "defined": True,
            **wilson_for_rate(true_positives, precision_n, confidence=confidence),
        }

    recall_block: dict[str, object]
    if recall_n == 0:
        recall_block = {
            "defined": False,
            "reason": "TP+FN=0 — recall undefined",
            "point": None,
        }
    else:
        recall_block = {
            "defined": True,
            **wilson_for_rate(true_positives, recall_n, confidence=confidence),
        }

    demonstrates = bool(
        precision_block.get("defined")
        and isinstance(precision_block.get("lower"), (int, float))
        and float(precision_block["lower"])  # type: ignore[arg-type]
        > INTERIM_CONFIRMED_FINDING_RATE_TARGET
    )
    return {
        "counts": {
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
        },
        "precision": precision_block,
        "recall": recall_block,
        "interim_confirmed_finding_rate_target": INTERIM_CONFIRMED_FINDING_RATE_TARGET,
        # Arithmetic-only: Wilson lower bound vs interim target. Never publishable
        # without RT-001 adjudicated customer corpus (Claims Lock).
        "demonstrates_interim_target": demonstrates,
        "demonstrates_interim_target_publishable": False,
        "demonstrates_interim_target_note": (
            "Arithmetic Wilson check only; not customer precision (RT-001)."
        ),
    }


def plan_sample_size(
    *,
    expected_p: float,
    margin: float,
    confidence: float = 0.95,
) -> dict[str, Any]:
    """Smallest n whose Wilson half-width at expected_p is ≤ margin."""

    alpha = _confidence_to_alpha(confidence)
    n = required_n_for_wilson_halfwidth(expected_p, half_width=margin, alpha=alpha)
    k = round(expected_p * n)
    interval = wilson_interval(k, n, alpha=alpha)
    return {
        "expected_p": expected_p,
        "margin": margin,
        "confidence": confidence,
        "alpha": alpha,
        "required_n": n,
        "preview_at_expected_p": interval.as_dict(),
        "method": "wilson_halfwidth_planner",
        "anchors": [
            "Wilson 1927 score interval",
            "Brown, Cai & DasGupta 2001 (Statistical Science) — Wilson recommended",
        ],
    }


def build_quality_protocol_stats(
    *,
    true_positives: int | None = None,
    false_positives: int | None = None,
    false_negatives: int | None = None,
    expected_p: float | None = None,
    margin: float | None = None,
    confidence: float = 0.95,
) -> dict[str, Any]:
    """Compose Wilson PR report and/or sample-size plan into one artifact."""

    has_counts = (
        true_positives is not None and false_positives is not None and false_negatives is not None
    )
    has_plan = expected_p is not None and margin is not None
    if not has_counts and not has_plan:
        raise ValueError(
            "provide TP/FP/FN counts and/or expected_p+margin for sample-size planning"
        )

    artifact: dict[str, Any] = {
        "artifact_type": "quality_protocol_stats",
        "schema_version": "1.0.0",
        "claim_boundary": CLAIM_BOUNDARY,
        "ranking_quality_reference": {
            "tool": "python -m aerobim.tools.evaluate_ranking_quality",
            "metric": "tie-aware nDCG@5/10/full with cluster-bootstrap CI",
            "note": (
                "nDCG is computed by evaluate_ranking_quality after graded "
                "adjudication; this tool does not recompute nDCG"
            ),
        },
        "protocol_doc": "docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md",
        "interim_confirmed_finding_rate_target": INTERIM_CONFIRMED_FINDING_RATE_TARGET,
    }
    if has_counts:
        assert true_positives is not None
        assert false_positives is not None
        assert false_negatives is not None
        artifact["wilson_precision_recall"] = compute_precision_recall_wilson(
            true_positives=true_positives,
            false_positives=false_positives,
            false_negatives=false_negatives,
            confidence=confidence,
        )
    if has_plan:
        assert expected_p is not None
        assert margin is not None
        artifact["sample_size_plan"] = plan_sample_size(
            expected_p=expected_p,
            margin=margin,
            confidence=confidence,
        )
    return artifact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tp", type=int, default=None, help="True positives")
    parser.add_argument("--fp", type=int, default=None, help="False positives")
    parser.add_argument("--fn", type=int, default=None, help="False negatives")
    parser.add_argument(
        "--expected-p",
        type=float,
        default=None,
        help="Planning assumption for sample-size Wilson half-width",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=None,
        help="Target Wilson half-width (e.g. 0.08)",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.95,
        help="Confidence level for Wilson intervals (default 0.95)",
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_quality_protocol_stats(
        true_positives=args.tp,
        false_positives=args.fp,
        false_negatives=args.fn,
        expected_p=args.expected_p,
        margin=args.margin,
        confidence=args.confidence,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
