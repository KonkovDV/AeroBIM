from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.domain.models import ComparisonOperator, RequirementSource, RuleScope, SourceKind
from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer


class NarrativeRuleSynthesizerTests(unittest.TestCase):
    def test_synthesize_extracts_area_and_fire_rating_rules(self) -> None:
        synthesizer = NarrativeRuleSynthesizer()

        requirements = synthesizer.synthesize(
            RequirementSource(
                text=(
                    "Помещение ROOM-101 должно иметь площадь не менее 42 м2\n"
                    "IFCWALL fire rating must be REI60\n"
                ),
                source_kind=SourceKind.TECHNICAL_SPECIFICATION,
                source_id="tz",
            )
        )

        self.assertEqual(len(requirements), 2)
        self.assertEqual(requirements[0].rule_scope, RuleScope.IFC_QUANTITY)
        self.assertEqual(requirements[0].target_ref, "ROOM-101")
        self.assertEqual(requirements[0].operator, ComparisonOperator.GREATER_OR_EQUAL)
        self.assertEqual(requirements[1].property_name, "FireRating")
        self.assertEqual(requirements[1].expected_value, "REI60")


if __name__ == "__main__":
    unittest.main()