"""Clash relevance triage (deterministic, advisory) — Jul 2026 practice wave.

External anchors: Ailem et al. 2026 (Automation in Construction, clash relevance
filtering); Koo et al. 2026 (ASCE JCEM). Claim boundary: no ML relevance model
is claimed; triage is presentation metadata and never flips summary.passed.
"""

from __future__ import annotations

import inspect
import random
import unittest

from aerobim.domain import clash_triage as clash_triage_module
from aerobim.domain.clash_triage import (
    ClashTriageBand,
    ClashTriageConfig,
    triage_clash_results,
)
from aerobim.domain.models import ClashResult, FindingCategory, Severity


def _clash(a: str, b: str, clash_type: str, distance: float) -> ClashResult:
    return ClashResult(
        element_a_guid=a,
        element_b_guid=b,
        clash_type=clash_type,
        distance=distance,
        description=f"{a} vs {b}",
    )


class ClashTriageBandTests(unittest.TestCase):
    def test_hard_depth_bands(self) -> None:
        cfg = ClashTriageConfig()
        self.assertEqual(cfg.band_for(_clash("a", "b", "hard", 0.060)), ClashTriageBand.CRITICAL)
        self.assertEqual(cfg.band_for(_clash("a", "b", "hard", 0.020)), ClashTriageBand.MAJOR)
        self.assertEqual(cfg.band_for(_clash("a", "b", "hard", 0.005)), ClashTriageBand.MINOR)
        self.assertEqual(cfg.band_for(_clash("a", "b", "hard", 0.0005)), ClashTriageBand.NEGLIGIBLE)

    def test_clearance_gap_bands(self) -> None:
        cfg = ClashTriageConfig()
        self.assertEqual(cfg.band_for(_clash("a", "b", "clearance", 0.001)), ClashTriageBand.MAJOR)
        self.assertEqual(cfg.band_for(_clash("a", "b", "clearance", 0.030)), ClashTriageBand.MINOR)


class ClashTriageDeterminismTests(unittest.TestCase):
    def test_output_independent_of_input_order(self) -> None:
        clashes = [
            _clash("w1", "p1", "hard", 0.060),
            _clash("w2", "p2", "hard", 0.012),
            _clash("w3", "p3", "clearance", 0.001),
            _clash("w4", "p4", "hard", 0.0004),
            _clash("w5", "p5", "clearance", 0.040),
        ]
        baseline = triage_clash_results(clashes)
        for seed in range(5):
            shuffled = list(clashes)
            random.Random(seed).shuffle(shuffled)
            self.assertEqual(triage_clash_results(shuffled), baseline)

    def test_symmetric_pair_dedup_keeps_worst(self) -> None:
        result = triage_clash_results(
            [
                _clash("duct", "pipe", "hard", 0.010),
                _clash("pipe", "duct", "hard", 0.055),
            ]
        )
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.duplicate_count, 1)
        item = result.items[0]
        self.assertEqual(item.band, ClashTriageBand.CRITICAL)
        self.assertEqual(item.clash.distance, 0.055)
        self.assertEqual(item.duplicates_merged, 2)
        self.assertEqual(item.pair_key, ("duct", "pipe"))

    def test_ranking_orders_bands_then_severity(self) -> None:
        result = triage_clash_results(
            [
                _clash("m1", "m2", "hard", 0.0002),
                _clash("c1", "c2", "hard", 0.070),
                _clash("j1", "j2", "hard", 0.015),
            ]
        )
        bands = [item.band for item in result.items]
        self.assertEqual(
            bands,
            [ClashTriageBand.CRITICAL, ClashTriageBand.MAJOR, ClashTriageBand.NEGLIGIBLE],
        )
        self.assertEqual([item.rank for item in result.items], [1, 2, 3])

    def test_no_clash_is_dropped(self) -> None:
        clashes = [_clash(f"a{i}", f"b{i}", "hard", 0.0001) for i in range(4)]
        result = triage_clash_results(clashes)
        self.assertEqual(len(result.items), 4)
        self.assertEqual(
            result.band_counts.get(ClashTriageBand.NEGLIGIBLE),
            4,
        )

    def test_rationale_is_atomic_and_verifiable(self) -> None:
        result = triage_clash_results([_clash("x", "y", "hard", 0.060)])
        rationale = result.items[0].rationale
        self.assertIn("depth=0.0600m", rationale)
        self.assertIn("critical>=0.0500m", rationale)
        self.assertIn("band=critical", rationale)


class SpatialPredicateTriageEnrichmentTests(unittest.TestCase):
    def test_issue_carries_triage_band_and_provenance(self) -> None:
        from aerobim.application.services.spatial_predicates import issues_from_clash_results

        issues = issues_from_clash_results(
            [_clash("duct", "pipe", "hard", 0.060)], affects_pass=False
        )
        self.assertEqual(len(issues), 1)
        issue = issues[0]
        self.assertEqual(issue.severity, Severity.WARNING)
        self.assertEqual(issue.category, FindingCategory.SPATIAL)
        self.assertEqual(issue.finding_id, "clash-hard-duct-pipe")
        self.assertEqual(issue.source_id, "clash")
        self.assertEqual(issue.origin, "deterministic")
        self.assertIn("triage:band=critical", issue.evidence_refs)
        self.assertIn("duct", issue.evidence_refs)
        self.assertIn("pipe", issue.evidence_refs)

    def test_symmetric_duplicates_merge_into_one_issue(self) -> None:
        from aerobim.application.services.spatial_predicates import issues_from_clash_results

        issues = issues_from_clash_results(
            [
                _clash("duct", "pipe", "hard", 0.010),
                _clash("pipe", "duct", "hard", 0.055),
            ]
        )
        self.assertEqual(len(issues), 1)
        self.assertIn("triage:duplicates_merged=2", issues[0].evidence_refs)

    def test_band_never_changes_severity_policy(self) -> None:
        from aerobim.application.services.spatial_predicates import issues_from_clash_results

        critical = _clash("a", "b", "hard", 0.900)
        soft = issues_from_clash_results([critical], affects_pass=False)
        self.assertEqual(soft[0].severity, Severity.WARNING)
        hard = issues_from_clash_results([critical], affects_pass=True)
        self.assertEqual(hard[0].severity, Severity.ERROR)


class ReviewPriorityTriageBoostTests(unittest.TestCase):
    def test_spatial_critical_outranks_spatial_negligible(self) -> None:
        from aerobim.application.services.spatial_predicates import issues_from_clash_results
        from aerobim.domain.review_priority import compute_issue_priority

        issues = issues_from_clash_results(
            [
                _clash("n1", "n2", "hard", 0.0002),
                _clash("c1", "c2", "hard", 0.070),
            ]
        )
        by_finding = {issue.finding_id: issue for issue in issues}
        critical_score = compute_issue_priority(by_finding["clash-hard-c1-c2"])
        negligible_score = compute_issue_priority(by_finding["clash-hard-n1-n2"])
        self.assertGreater(critical_score, negligible_score)

    def test_non_spatial_issue_gets_no_triage_boost(self) -> None:
        from aerobim.domain.models import ValidationIssue
        from aerobim.domain.review_priority import compute_issue_priority

        issue = ValidationIssue(
            rule_id="XDOC-001",
            severity=Severity.WARNING,
            message="cross",
            category=FindingCategory.CROSS_DOCUMENT,
            evidence_refs=("triage:band=critical",),
        )
        self.assertEqual(compute_issue_priority(issue), 35)


class ClashTriageClaimBoundaryTests(unittest.TestCase):
    def test_module_never_claims_ml_relevance_or_lin_score(self) -> None:
        source = inspect.getsource(clash_triage_module)
        self.assertIn("no ML relevance model is claimed", source)
        self.assertNotIn("0.96", source)

    def test_module_never_touches_summary_passed(self) -> None:
        source = inspect.getsource(clash_triage_module)
        self.assertNotIn("summary.passed", source.replace("``summary.passed``", ""))
        self.assertNotIn("ValidationSummary", source)
        self.assertNotIn("PackageOutcome", source)


if __name__ == "__main__":
    unittest.main()
