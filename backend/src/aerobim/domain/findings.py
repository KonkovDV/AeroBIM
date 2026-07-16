"""Finding predicates — distinct claim classes for per-type precision metrics."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from enum import StrEnum

from aerobim.domain.models import ConflictKind, FindingCategory, ValidationIssue


class FindingPredicate(StrEnum):
    """Typed finding predicates; never roll into a single opaque accuracy number."""

    GEOMETRIC_CLASH = "geometric_clash"
    NORM_VIOLATION = "norm_violation"
    CROSS_DOCUMENT = "cross_document"
    IDS_FACET = "ids_facet"
    DRAWING_MEASURE = "drawing_measure"
    SCHEMA_GATE = "schema_gate"
    VERSION_MISMATCH = "version_mismatch"
    OTHER = "other"


def predicate_for_issue(issue: ValidationIssue) -> FindingPredicate:
    """Map a ValidationIssue onto a stable predicate for per-type metrics."""

    if issue.conflict_kind is ConflictKind.VERSION_MISMATCH:
        return FindingPredicate.VERSION_MISMATCH
    if issue.category is FindingCategory.SPATIAL:
        return FindingPredicate.GEOMETRIC_CLASH
    if issue.category is FindingCategory.CROSS_DOCUMENT:
        return FindingPredicate.CROSS_DOCUMENT
    if issue.category is FindingCategory.IDS_VALIDATION:
        return FindingPredicate.IDS_FACET
    if issue.category is FindingCategory.DRAWING_VALIDATION:
        return FindingPredicate.DRAWING_MEASURE

    rule = (issue.rule_id or "").casefold()
    if rule.startswith("aerobim-revision") or "version-mismatch" in rule:
        return FindingPredicate.VERSION_MISMATCH
    if rule.startswith("aerobim-norm") or rule.startswith("norm-") or "norm_pack" in rule:
        return FindingPredicate.NORM_VIOLATION
    if rule.startswith("schema") or "ifc-schema" in rule or rule.startswith("bsi-"):
        return FindingPredicate.SCHEMA_GATE
    # IFC property failures against pack/norm rules often carry SP-/GOST- prefixes.
    if "сп" in rule or "sp." in rule or "gost" in rule or "norm" in rule:
        return FindingPredicate.NORM_VIOLATION
    if issue.category is FindingCategory.IFC_VALIDATION:
        return FindingPredicate.NORM_VIOLATION
    return FindingPredicate.OTHER


def per_predicate_counts(issues: Iterable[ValidationIssue]) -> dict[str, int]:
    """Count issues by FindingPredicate value (stable keys for reports/metrics)."""

    counter: Counter[str] = Counter()
    for issue in issues:
        counter[predicate_for_issue(issue).value] += 1
    return dict(sorted(counter.items()))


def per_predicate_metrics(
    issues: Iterable[ValidationIssue],
) -> dict[str, dict[str, int | float]]:
    """Lightweight per-type rollup: count + share of total (not publishable precision)."""

    counts = per_predicate_counts(issues)
    total = sum(counts.values())
    metrics: dict[str, dict[str, int | float]] = {}
    for predicate, count in counts.items():
        share = (count / total) if total else 0.0
        metrics[predicate] = {"count": count, "share": round(share, 6)}
    return metrics


__all__ = [
    "FindingPredicate",
    "per_predicate_counts",
    "per_predicate_metrics",
    "predicate_for_issue",
]
