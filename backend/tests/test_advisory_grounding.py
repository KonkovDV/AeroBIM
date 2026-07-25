"""Advisory evidence grounding (Wave J, Jul 2026).

Anchors: TACO (EACL 2026) verified atomic claims; Chain-of-Verification;
FinGround atomic verification against evidence. Claim boundary: grounding
stamps and demotions are advisory-contour metadata — they never raise
severity, never write summary.passed, and never drop a finding.
"""

from __future__ import annotations

import unittest

from aerobim.application.services.determinism_gate import (
    DeterminismGate,
    build_evidence_universe,
)
from aerobim.domain.models import (
    ClashResult,
    FindingCategory,
    ParsedRequirement,
    Severity,
    ValidationIssue,
)


def _advisory(guid: str | None, target: str | None = None) -> ValidationIssue:
    return ValidationIssue(
        rule_id="AI-ADVISORY-001",
        severity=Severity.ERROR,
        message="advisory claim",
        category=FindingCategory.IFC_VALIDATION,
        element_guid=guid,
        target_ref=target,
        origin="advisory",
    )


def _engine(guid: str) -> ValidationIssue:
    return ValidationIssue(
        rule_id="IDS-001",
        severity=Severity.ERROR,
        message="engine finding",
        category=FindingCategory.IDS_VALIDATION,
        element_guid=guid,
    )


class EvidenceUniverseTests(unittest.TestCase):
    def test_universe_collects_engine_requirement_clash_annotation_tokens(self) -> None:
        requirement = ParsedRequirement(
            rule_id="REQ-FIRE-01",
            ifc_entity="IFCWALL",
            rule_scope="entity",
            target_ref="WALL-01",
            property_set=None,
            property_name="FireRating",
            operator="gte",
            expected_value="REI60",
            unit=None,
            source="tz",
        )
        clash = ClashResult(
            element_a_guid="guid-clash-a",
            element_b_guid="guid-clash-b",
            clash_type="hard",
            distance=0.02,
            description="x",
        )
        universe = build_evidence_universe(
            engine_issues=(_engine("guid-engine-1"),),
            requirements=(requirement,),
            clash_results=(clash,),
        )
        for token in (
            "guid-engine-1",
            "REQ-FIRE-01",
            "WALL-01",
            "IFCWALL",
            "guid-clash-a",
            "guid-clash-b",
        ):
            self.assertIn(token, universe)


class AdvisoryGroundingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gate = DeterminismGate()
        self.universe = frozenset({"guid-known", "WALL-01"})

    def test_grounded_reference_is_stamped_verified(self) -> None:
        merged, divergences = self.gate.reconcile(
            engine_issues=(),
            advisory_issues=(_advisory("guid-known"),),
            evidence_universe=self.universe,
        )
        issue = merged[0]
        self.assertEqual(issue.severity, Severity.INFO)
        self.assertIn("grounding:verified_reference", issue.evidence_refs)
        self.assertNotIn("[ungrounded]", issue.message)
        self.assertFalse(divergences[0].advisory_verdict.startswith("ungrounded:"))

    def test_unknown_reference_is_stamped_ungrounded(self) -> None:
        merged, divergences = self.gate.reconcile(
            engine_issues=(),
            advisory_issues=(_advisory("guid-hallucinated"),),
            evidence_universe=self.universe,
        )
        issue = merged[0]
        self.assertEqual(issue.severity, Severity.INFO)
        self.assertIn("grounding:unverified_reference", issue.evidence_refs)
        self.assertIn("[ungrounded]", issue.message)
        self.assertIn("guid-hallucinated", issue.message)
        self.assertTrue(divergences[0].advisory_verdict.startswith("ungrounded:"))

    def test_no_reference_is_stamped_explicitly(self) -> None:
        merged, _ = self.gate.reconcile(
            engine_issues=(),
            advisory_issues=(_advisory(None),),
            evidence_universe=self.universe,
        )
        self.assertIn("grounding:no_verifiable_reference", merged[0].evidence_refs)

    def test_grounding_never_raises_severity_or_drops_findings(self) -> None:
        merged, _ = self.gate.reconcile(
            engine_issues=(),
            advisory_issues=(
                _advisory("guid-hallucinated"),
                _advisory("guid-known"),
                _advisory(None),
            ),
            evidence_universe=self.universe,
        )
        self.assertEqual(len(merged), 3)
        self.assertTrue(all(issue.severity == Severity.INFO for issue in merged))

    def test_without_universe_behavior_is_unchanged(self) -> None:
        merged, _ = self.gate.reconcile(
            engine_issues=(),
            advisory_issues=(_advisory("guid-hallucinated"),),
        )
        issue = merged[0]
        self.assertNotIn("[ungrounded]", issue.message)
        self.assertFalse(any(str(ref).startswith("grounding:") for ref in issue.evidence_refs))


if __name__ == "__main__":
    unittest.main()
