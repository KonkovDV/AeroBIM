"""One-command pilot harness: agreement + precision + ranking in one run.

Closes the Checkpoint #2 DoD item (stream 4): "Harness одной командой даёт
precision/recall/F1/FP-rate (+ κ из CSV); nDCG — если реализован". This tool
is pure orchestration over the existing, individually-tested evaluators —
it introduces **no new statistical semantics**:

- ``measure_adjudication_csv``  → κ / α agreement artifact
- ``evaluate_detection_precision`` → TP/FP/FN, precision/recall/F1,
  FP-burden, per-discipline / per-class breakdowns, publishable gate
- ``evaluate_ranking_quality`` (optional) → tie-aware nDCG@5/10/full + CI

Outputs one ``pilot_harness_report`` JSON plus the individual artifacts in
``--output``. Exit code 1 when ``--require-publishable`` is set and the
precision claim fails the publishable protocol gate (customer corpus +
≥2 adjudicators + held-out + FN tracking + agreement thresholds).

Claim boundary: the harness aggregates; it never upgrades dataset_status —
fixture/synthetic runs stay non-publishable by the underlying gates (RT-001).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from aerobim.tools.evaluate_detection_precision import evaluate_detection_precision
from aerobim.tools.evaluate_ranking_quality import evaluate_ranking_quality
from aerobim.tools.measure_adjudicator_agreement import measure_adjudication_csv


def run_pilot_harness(
    *,
    labels_path: Path,
    detections_path: Path,
    adjudication_csv: Path | None = None,
    ranking_labels_path: Path | None = None,
    output_dir: Path | None = None,
    require_publishable: bool = False,
) -> dict[str, Any]:
    """Run all pilot evaluators once; return the combined artifact."""

    agreement: dict[str, Any] | None = None
    agreement_file: Path | None = None
    if adjudication_csv is not None:
        agreement = dict(measure_adjudication_csv(adjudication_csv))
        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            agreement_file = output_dir / "agreement.json"
            agreement_file.write_text(
                json.dumps(agreement, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

    precision = evaluate_detection_precision(
        labels_path,
        detections_path,
        require_publishable=require_publishable,
        agreement_path=agreement_file,
        require_agreement_for_publishable=agreement_file is not None,
    )

    ranking: dict[str, Any] | None = None
    if ranking_labels_path is not None:
        ranking = evaluate_ranking_quality(ranking_labels_path)

    claim = precision.get("precision_claim")
    publishable = bool(claim.get("publishable")) if isinstance(claim, dict) else False
    combined: dict[str, Any] = {
        "artifact_type": "pilot_harness_report",
        "schema_version": "1.0.0",
        "inputs": {
            "labels": str(labels_path),
            "detections": str(detections_path),
            "adjudication_csv": str(adjudication_csv) if adjudication_csv else None,
            "ranking_labels": str(ranking_labels_path) if ranking_labels_path else None,
        },
        "agreement": agreement,
        "precision": precision,
        "ranking": ranking,
        "publishable": publishable,
        "claim_boundary": (
            "aggregation only; dataset_status gates are enforced by the "
            "underlying evaluators — fixture/synthetic runs are never "
            "publishable product accuracy (RT-001)"
        ),
    }

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "precision-report.json").write_text(
            json.dumps(precision, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        if ranking is not None:
            (output_dir / "ranking-report.json").write_text(
                json.dumps(ranking, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
        (output_dir / "pilot-harness-report.json").write_text(
            json.dumps(combined, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    return combined


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--detections", type=Path, required=True)
    parser.add_argument("--adjudication-csv", type=Path, default=None)
    parser.add_argument("--ranking-labels", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--require-publishable",
        action="store_true",
        help="Exit 1 unless the precision claim passes the publishable protocol gate",
    )
    args = parser.parse_args(argv)
    try:
        combined = run_pilot_harness(
            labels_path=args.labels.resolve(),
            detections_path=args.detections.resolve(),
            adjudication_csv=args.adjudication_csv.resolve() if args.adjudication_csv else None,
            ranking_labels_path=args.ranking_labels.resolve() if args.ranking_labels else None,
            output_dir=args.output.resolve() if args.output else None,
            require_publishable=args.require_publishable,
        )
    except ValueError as exc:
        # evaluate_detection_precision raises on a failed publishable gate.
        print(f"pilot harness gate failure: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(combined, ensure_ascii=False, indent=2))
    if args.require_publishable and not combined["publishable"]:
        print("PrecisionClaim is not publishable.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
