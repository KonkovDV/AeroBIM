"""Finding predicate mapping and per-type metrics."""

from __future__ import annotations

import unittest

from aerobim.domain.findings import (
    FindingPredicate,
    per_predicate_counts,
    per_predicate_metrics,
    predicate_for_issue,
)
from aerobim.domain.models import ConflictKind, FindingCategory, Severity, ValidationIssue


def _issue(
    *,
    rule_id: str = "X",
    category: FindingCategory = FindingCategory.IFC_VALIDATION,
    conflict_kind: ConflictKind | None = None,
) -> ValidationIssue:
    return ValidationIssue(
        rule_id=rule_id,
        severity=Severity.ERROR,
        message="test",
        category=category,
        conflict_kind=conflict_kind,
    )


class FindingPredicateTests(unittest.TestCase):
    def test_maps_spatial_to_geometric_clash(self) -> None:
        self.assertEqual(
            predicate_for_issue(_issue(category=FindingCategory.SPATIAL)),
            FindingPredicate.GEOMETRIC_CLASH,
        )

    def test_maps_version_mismatch(self) -> None:
        self.assertEqual(
            predicate_for_issue(
                _issue(
                    rule_id="AEROBIM-REVISION-MERGE",
                    category=FindingCategory.CROSS_DOCUMENT,
                    conflict_kind=ConflictKind.VERSION_MISMATCH,
                )
            ),
            FindingPredicate.VERSION_MISMATCH,
        )

    def test_maps_ifc_to_norm_violation(self) -> None:
        self.assertEqual(
            predicate_for_issue(
                _issue(rule_id="SP-54-HEIGHT", category=FindingCategory.IFC_VALIDATION)
            ),
            FindingPredicate.NORM_VIOLATION,
        )

    def test_per_type_counts_and_shares(self) -> None:
        issues = [
            _issue(category=FindingCategory.SPATIAL),
            _issue(category=FindingCategory.SPATIAL),
            _issue(category=FindingCategory.IDS_VALIDATION),
        ]
        counts = per_predicate_counts(issues)
        self.assertEqual(counts[FindingPredicate.GEOMETRIC_CLASH.value], 2)
        self.assertEqual(counts[FindingPredicate.IDS_FACET.value], 1)
        metrics = per_predicate_metrics(issues)
        self.assertAlmostEqual(
            float(metrics[FindingPredicate.GEOMETRIC_CLASH.value]["share"]),
            2 / 3,
            places=5,
        )


if __name__ == "__main__":
    unittest.main()
