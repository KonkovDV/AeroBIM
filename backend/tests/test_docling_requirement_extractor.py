from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.domain.models import ComparisonOperator, RequirementSource, RuleScope, SourceKind
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)


class StructuredRequirementExtractorTests(unittest.TestCase):
    def test_extract_parses_pipe_separated_requirement_rows(self) -> None:
        extractor = StructuredRequirementExtractor()

        requirements = extractor.extract(
            RequirementSource(
                text=(
                    "# rule_id|entity|property_set|property_name|expected_value\n"
                    "REQ-100|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                )
            )
        )

        self.assertEqual(len(requirements), 1)
        self.assertEqual(requirements[0].rule_id, "REQ-100")
        self.assertEqual(requirements[0].ifc_entity, "IFCWALL")
        self.assertEqual(requirements[0].property_set, "Pset_WallCommon")
        self.assertEqual(requirements[0].property_name, "FireRating")
        self.assertEqual(requirements[0].expected_value, "REI60")
        self.assertEqual(requirements[0].source_kind, SourceKind.STRUCTURED_TEXT)

    def test_extract_parses_extended_requirement_rows(self) -> None:
        extractor = StructuredRequirementExtractor()

        requirements = extractor.extract(
            RequirementSource(
                text=(
                    "REQ-AREA-001|ifc-quantity|IFCSPACE|ROOM-101|Qto_SpaceBaseQuantities|NetFloorArea|gte|42|m2|Area from TZ\n"
                )
            )
        )

        self.assertEqual(len(requirements), 1)
        self.assertEqual(requirements[0].rule_scope, RuleScope.IFC_QUANTITY)
        self.assertEqual(requirements[0].target_ref, "ROOM-101")
        self.assertEqual(requirements[0].operator, ComparisonOperator.GREATER_OR_EQUAL)
        self.assertEqual(requirements[0].unit, "m2")


if __name__ == "__main__":
    unittest.main()
