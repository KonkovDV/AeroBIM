"""CLI for extraction quality evaluation against ground-truth manifests."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from aerobim.application.services.extraction_benchmark import evaluate_fixture
from aerobim.domain.models import RequirementSource, SourceKind
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer


def _default_manifest_path() -> Path:
    return (
        Path(__file__).resolve().parents[3].parent
        / "samples"
        / "benchmarks"
        / "russian-aec-ground-truth.json"
    )


def _evaluate_manifest(manifest_path: Path) -> dict[str, object]:
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)

    structured_extractor = StructuredRequirementExtractor()
    narrative_synthesizer = NarrativeRuleSynthesizer()
    base_dir = manifest_path.parent.parent.parent

    fixture_results = []
    total_tp = total_fp = total_fn = 0

    for fixture in manifest["fixtures"]:
        fixture_id = fixture["fixture_id"]
        source_path = base_dir / fixture["source_path"]
        gt_requirements = fixture["ground_truth_requirements"]
        source_kind = str(fixture.get("source_kind") or SourceKind.STRUCTURED_TEXT.value)
        source = RequirementSource(
            path=source_path,
            source_kind=SourceKind(source_kind)
            if source_kind in {item.value for item in SourceKind}
            else SourceKind.STRUCTURED_TEXT,
        )

        if source_kind in {
            SourceKind.TECHNICAL_SPECIFICATION.value,
            SourceKind.CALCULATION.value,
            SourceKind.INLINE_TEXT.value,
        }:
            extracted = narrative_synthesizer.synthesize(source)
        else:
            extracted = structured_extractor.extract(source)

        result = evaluate_fixture(fixture_id, extracted, gt_requirements)
        fixture_results.append(result)
        total_tp += result.true_positives
        total_fp += result.false_positives
        total_fn += result.false_negatives

    micro_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    micro_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    micro_f1 = (
        (2 * micro_precision * micro_recall / (micro_precision + micro_recall))
        if (micro_precision + micro_recall) > 0
        else 0.0
    )

    n = len(fixture_results)
    macro_precision = sum(r.precision for r in fixture_results) / n if n > 0 else 0.0
    macro_recall = sum(r.recall for r in fixture_results) / n if n > 0 else 0.0
    macro_f1 = sum(r.f1_score for r in fixture_results) / n if n > 0 else 0.0

    discipline_buckets: dict[str, list] = {}
    for fixture, result in zip(manifest["fixtures"], fixture_results, strict=True):
        discipline = str(fixture.get("discipline") or "unknown")
        discipline_buckets.setdefault(discipline, []).append(result)

    per_discipline: dict[str, dict[str, float]] = {}
    for discipline, results in sorted(discipline_buckets.items()):
        per_discipline[discipline] = {
            "fixture_count": float(len(results)),
            "macro_precision": sum(r.precision for r in results) / len(results),
            "macro_recall": sum(r.recall for r in results) / len(results),
            "macro_f1": sum(r.f1_score for r in results) / len(results),
        }

    return {
        "artifact_type": "extraction_quality_report",
        "manifest": str(manifest_path.resolve()),
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": macro_f1,
        "micro_precision": micro_precision,
        "micro_recall": micro_recall,
        "micro_f1": micro_f1,
        "per_discipline": per_discipline,
        "fixtures": [
            {
                "fixture_id": result.fixture_id,
                "true_positives": result.true_positives,
                "false_positives": result.false_positives,
                "false_negatives": result.false_negatives,
                "precision": result.precision,
                "recall": result.recall,
                "f1_score": result.f1_score,
            }
            for result in fixture_results
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate requirement extraction quality (P/R/F1)."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=_default_manifest_path(),
        help="Ground-truth manifest JSON path",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write JSON metrics artifact",
    )
    parser.add_argument(
        "--min-macro-f1",
        type=float,
        default=None,
        help="Exit with code 1 if macro F1 is below this threshold (advisory gate)",
    )
    args = parser.parse_args(argv)

    manifest_path = args.manifest.resolve()
    if not manifest_path.exists():
        print(f"Manifest not found: {manifest_path}", file=sys.stderr)
        return 1

    payload = _evaluate_manifest(manifest_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {args.output}", file=sys.stderr)

    macro_f1 = float(payload["macro_f1"])
    if args.min_macro_f1 is not None and macro_f1 < args.min_macro_f1:
        print(
            f"macro_f1 {macro_f1:.3f} below threshold {args.min_macro_f1:.3f}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
