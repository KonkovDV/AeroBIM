from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.application.services.loin_metadata_resolver import LoinMetadataResolver
from aerobim.domain.models import ComparisonOperator, ParsedRequirement, RuleScope, SourceKind
from aerobim.infrastructure.adapters.bsdd_term_mapper import BsddTermMapper


class AcademicBsddLoinTests(unittest.TestCase):
    def test_bsdd_mapper_resolves_pilot_property_names(self) -> None:
        mapper = BsddTermMapper()
        pilot_properties = [
            "FireRating",
            "ThermalTransmittance",
            "Thickness",
            "ConcreteStrengthClass",
            "ThermalConductivity",
        ]
        resolved = sum(1 for name in pilot_properties if mapper.resolve_uri(name) is not None)
        self.assertGreaterEqual(resolved / len(pilot_properties), 0.8)

    def test_loin_metadata_attached_for_cross_doc_rules(self) -> None:
        resolver = LoinMetadataResolver()
        metadata = resolver.resolve("CROSS-DOC-IfcWall-FireRating")
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.purpose, "coordination")  # type: ignore[union-attr]

    def test_enrich_adds_bsdd_uri(self) -> None:
        mapper = BsddTermMapper()
        requirement = ParsedRequirement(
            rule_id="test-001",
            ifc_entity="IfcWall",
            property_name="FireRating",
            expected_value="REI120",
            rule_scope=RuleScope.IFC_PROPERTY,
            operator=ComparisonOperator.GREATER_OR_EQUAL,
            source_kind=SourceKind.TECHNICAL_SPECIFICATION,
        )
        enriched = mapper.enrich(requirement)
        self.assertIsNotNone(enriched.bsdd_uri)


if __name__ == "__main__":
    unittest.main()
