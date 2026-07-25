"""Plan the adjudicated labeling corpus for the pilot precision threshold.

One command answers "сколько размечать двум экспертам": given the interim
threshold (default TP/(TP+FP) >= 0.60), an honest planning assumption for
the true precision, alpha and target power, the tool reports:

1. the smallest corpus where the exact one-sided binomial test can
   demonstrate p > threshold with the requested power (Miller 2024 norm:
   evals need power analysis, not vibes), and
2. the smallest corpus where the Wilson interval (Brown-Cai-DasGupta 2001
   recommendation) reaches the requested half-width at the expected rate,
3. a preview of Wilson intervals for plausible observed counts at the
   recommended n — so the labeling instruction can pre-register what
   "confirmed" will look like before any customer data arrives.

Claim boundary: this sizes labeling effort only; it predicts nothing about
actual precision and never upgrades fixture evidence (RT-001).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from aerobim.domain.study_design import (
    binomial_power_one_sided,
    required_n_for_power,
    required_n_for_wilson_halfwidth,
    wilson_interval,
)


def plan_adjudication_corpus(
    *,
    threshold: float = 0.60,
    expected_precision: float = 0.75,
    alpha: float = 0.05,
    power: float = 0.80,
    ci_half_width: float = 0.08,
) -> dict[str, Any]:
    """Deterministic corpus plan artifact (pure computation, no I/O)."""

    if expected_precision <= threshold:
        raise ValueError(
            "expected_precision must exceed threshold — otherwise the study "
            "cannot demonstrate the threshold at any n"
        )

    power_design = required_n_for_power(
        p0=threshold,
        p_true=expected_precision,
        alpha=alpha,
        power=power,
    )
    width_n = required_n_for_wilson_halfwidth(
        expected_precision,
        half_width=ci_half_width,
        alpha=alpha,
    )
    recommended_n = max(power_design.n, width_n)

    # Pre-registered decision preview at the recommended corpus size.
    preview: list[dict[str, object]] = []
    for rate in (threshold, expected_precision, min(0.95, expected_precision + 0.10)):
        successes = round(rate * recommended_n)
        interval = wilson_interval(successes, recommended_n, alpha=alpha)
        preview.append(
            {
                "planning_rate": rate,
                **interval.as_dict(),
                "demonstrates_threshold": interval.lower > threshold,
            }
        )

    return {
        "artifact_type": "adjudication_corpus_plan",
        "schema_version": "1.0.0",
        "inputs": {
            "threshold": threshold,
            "expected_precision": expected_precision,
            "alpha": alpha,
            "target_power": power,
            "ci_half_width": ci_half_width,
        },
        "power_design": power_design.as_dict(),
        "wilson_width_n": width_n,
        "recommended_n": recommended_n,
        "recommended_n_note": (
            "max(power design, CI-width design); exact binomial power is "
            "sawtoothed in n — nearby n are equivalent design points"
        ),
        "decision_preview_at_recommended_n": preview,
        "anchors": [
            "Wilson 1927 score interval",
            "Brown, Cai & DasGupta 2001 (Statistical Science) — Wilson recommended",
            "Miller 2024 arXiv 2411.00640 — power analysis for evals",
        ],
        "claim_boundary": (
            "sizes the dual-expert labeling effort only; predicts no "
            "precision value; fixture evidence never becomes customer "
            "evidence (RT-001)"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold", type=float, default=0.60)
    parser.add_argument("--expected-precision", type=float, default=0.75)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--power", type=float, default=0.80)
    parser.add_argument("--ci-half-width", type=float, default=0.08)
    parser.add_argument("--n", type=int, default=None, help="Evaluate a fixed n instead")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.n is not None:
        result = binomial_power_one_sided(
            n=args.n,
            p0=args.threshold,
            p_true=args.expected_precision,
            alpha=args.alpha,
        )
        report: dict[str, Any] = {
            "artifact_type": "adjudication_corpus_plan",
            "schema_version": "1.0.0",
            "fixed_n_evaluation": result.as_dict(),
        }
    else:
        report = plan_adjudication_corpus(
            threshold=args.threshold,
            expected_precision=args.expected_precision,
            alpha=args.alpha,
            power=args.power,
            ci_half_width=args.ci_half_width,
        )
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
