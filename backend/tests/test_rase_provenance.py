from __future__ import annotations

import unittest

from aerobim.domain.models import ParsedRequirement, RuleScope, Severity, issue_from_requirement
from aerobim.domain.rase import format_rase_summary, infer_rase_elements
from aerobim.infrastructure.adapters.deterministic_requirement_to_ids_compiler import (
    DeterministicRequirementToIdsCompiler,
)


class RaseProvenanceTests(unittest.TestCase):
    def test_infer_rase_for_property_rule(self) -> None:
        req = ParsedRequirement(
            rule_id="R1",
            ifc_entity="IFCWALL",
            property_set="Pset_WallCommon",
            property_name="IsExternal",
            expected_value="TRUE",
            rule_scope=RuleScope.IFC_PROPERTY,
        )
        self.assertEqual(infer_rase_elements(req), ("R", "A", "S"))
        self.assertIn("R+A+S", format_rase_summary(("R", "A", "S")))

    def test_issue_from_requirement_stamps_rase(self) -> None:
        req = ParsedRequirement(
            rule_id="R1",
            ifc_entity="IFCWALL",
            property_name="LoadBearing",
            expected_value="TRUE",
            rule_scope=RuleScope.IFC_PROPERTY,
            norm_clause="5.2.1",
        )
        issue = issue_from_requirement(req, severity=Severity.WARNING, message="missing")
        self.assertEqual(issue.rase_elements, ("R", "A", "S"))
        self.assertEqual(issue.norm_clause, "5.2.1")

    def test_ids_compile_draft_carries_rase(self) -> None:
        compiler = DeterministicRequirementToIdsCompiler()
        req = ParsedRequirement(
            rule_id="R1",
            ifc_entity="IFCWALL",
            property_set="Pset_WallCommon",
            property_name="IsExternal",
            expected_value="TRUE",
            rule_scope=RuleScope.IFC_PROPERTY,
        )
        draft = compiler.compile_requirements([req])
        self.assertTrue(draft.advisory_only)
        self.assertEqual(draft.rase_elements, ("R", "A", "S"))
        self.assertIsNotNone(draft.rase_summary)
        self.assertIn("<ids", draft.suggested_ids_xml)


if __name__ == "__main__":
    unittest.main()
