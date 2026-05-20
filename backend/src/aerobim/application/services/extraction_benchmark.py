"""Extraction quality benchmark harness for AeroBIM.

Computes precision, recall, and F1-score by comparing extracted
``ParsedRequirement`` instances against a ground-truth manifest.

Matching rules:
- A requirement matches ground truth when ``ifc_entity``, ``property_name``,
  and ``expected_value`` all agree (case-insensitive).
- ``property_set`` is checked when present in ground truth.
- ``unit`` is checked when present in both (case-insensitive).

Scope: Russian AEC fixture evaluation (Phase 2).
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from aerobim.domain.models import ParsedRequirement


@dataclass(frozen=True)
class ExtractionMetricResult:
    """Metrics for a single fixture evaluation."""

    fixture_id: str
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float


@dataclass(frozen=True)
class ExtractionBenchmarkSummary:
    """Aggregated benchmark results across all fixtures."""

    fixture_results: Sequence[ExtractionMetricResult]
    total_true_positives: int
    total_false_positives: int
    total_false_negatives: int
    macro_precision: float
    macro_recall: float
    macro_f1: float
    micro_precision: float
    micro_recall: float
    micro_f1: float


def _normalize_ifc_entity(value: object) -> str:
    if value is None:
        return ""
    normalized = str(value).strip().lower()
    if normalized.startswith("ifc"):
        return normalized
    return f"ifc{normalized}"


def _requirement_matches(
    extracted: ParsedRequirement,
    ground_truth: dict,
) -> bool:
    """Check if an extracted requirement matches a ground-truth entry."""
    extracted_entity = _normalize_ifc_entity(extracted.ifc_entity)
    ground_entity = _normalize_ifc_entity(ground_truth.get("ifc_entity"))
    if extracted_entity != ground_entity:
        return False
    gt_property = (ground_truth.get("property_name") or "").lower()
    if (extracted.property_name or "").lower() != gt_property:
        return False
    if (extracted.expected_value or "").lower() != (
        ground_truth.get("expected_value") or ""
    ).lower():
        return False
    gt_property_set = ground_truth.get("property_set")
    if gt_property_set is not None:
        if (extracted.property_set or "").lower() != gt_property_set.lower():
            return False
    gt_unit = ground_truth.get("unit")
    if gt_unit is not None and extracted.unit is not None:
        if extracted.unit.strip().lower() != gt_unit.strip().lower():
            return False
    return True


def _match_requirements(
    extracted: Sequence[ParsedRequirement],
    ground_truth: Sequence[dict],
) -> tuple[int, int, int]:
    """Return (true_positives, false_positives, false_negatives)."""
    matched_gt: set[int] = set()
    true_positives = 0

    for ext in extracted:
        found = False
        for idx, gt in enumerate(ground_truth):
            if idx in matched_gt:
                continue
            if _requirement_matches(ext, gt):
                matched_gt.add(idx)
                found = True
                true_positives += 1
                break
        if not found:
            true_positives += 0  # explicit no-op for clarity; this is a false positive

    false_positives = len(extracted) - true_positives
    false_negatives = len(ground_truth) - len(matched_gt)
    return true_positives, false_positives, false_negatives


def evaluate_fixture(
    fixture_id: str,
    extracted: Sequence[ParsedRequirement],
    ground_truth: Sequence[dict],
) -> ExtractionMetricResult:
    """Evaluate a single fixture and return per-fixture metrics."""
    tp, fp, fn = _match_requirements(extracted, ground_truth)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return ExtractionMetricResult(
        fixture_id=fixture_id,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        precision=precision,
        recall=recall,
        f1_score=f1,
    )


def run_extraction_benchmark(
    ground_truth_path: Path,
    extract_fn,
) -> ExtractionBenchmarkSummary:
    """Run the full benchmark suite against a ground-truth manifest.

    ``extract_fn`` is a callable that receives a file path and returns an
    iterable of ``ParsedRequirement`` instances (e.g. the structured
    requirement extractor).
    """
    with open(ground_truth_path, encoding="utf-8") as fh:
        manifest = json.load(fh)

    fixture_results: list[ExtractionMetricResult] = []
    total_tp = total_fp = total_fn = 0

    base_dir = ground_truth_path.parent.parent.parent
    for fixture in manifest["fixtures"]:
        fixture_id = fixture["fixture_id"]
        source_path = base_dir / fixture["source_path"]
        gt_requirements = fixture["ground_truth_requirements"]

        extracted = list(extract_fn(source_path))
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

    return ExtractionBenchmarkSummary(
        fixture_results=tuple(fixture_results),
        total_true_positives=total_tp,
        total_false_positives=total_fp,
        total_false_negatives=total_fn,
        macro_precision=macro_precision,
        macro_recall=macro_recall,
        macro_f1=macro_f1,
        micro_precision=micro_precision,
        micro_recall=micro_recall,
        micro_f1=micro_f1,
    )
