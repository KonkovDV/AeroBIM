from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.domain.models import FindingCategory, Severity


class IfcTesterIdsValidatorResultMappingTests(unittest.TestCase):
    """Tests for IDS result-to-domain mapping without requiring ifcopenshell."""

    def test_extract_guid_reads_globalid_from_entity_instance_like_object(self) -> None:
        from aerobim.infrastructure.adapters.ifc_tester_ids_validator import IfcTesterIdsValidator

        class FakeEntity:
            GlobalId = "2hJQkZ0zj1XBp0001"

        validator = IfcTesterIdsValidator()

        self.assertEqual(
            validator._extract_guid(FakeEntity()),
            "2hJQkZ0zj1XBp0001",
        )

    def test_map_results_extracts_failed_entities(self) -> None:
        from aerobim.infrastructure.adapters.ifc_tester_ids_validator import IfcTesterIdsValidator

        validator = IfcTesterIdsValidator()
        fake_results = {
            "specifications": [
                {
                    "name": "Wall Fire Rating",
                    "status": False,
                    "requirements": [
                        {
                            "facet_type": "Property",
                            "description": "Pset_WallCommon.FireRating must be REI60",
                            "status": False,
                            "failed_entities": [
                                {
                                    "element": "2hJQkZ0zj1XBp0001#42",
                                    "reason": "Value is REI30, expected REI60",
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        issues = validator._map_results(fake_results)

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].severity, Severity.ERROR)
        self.assertEqual(issues[0].category, FindingCategory.IDS_VALIDATION)
        self.assertIn("Wall Fire Rating", issues[0].rule_id)
        self.assertIn("REI30", issues[0].message)
        self.assertEqual(issues[0].element_guid, "2hJQkZ0zj1XBp0001")

    def test_map_results_skips_passing_specs(self) -> None:
        from aerobim.infrastructure.adapters.ifc_tester_ids_validator import IfcTesterIdsValidator

        validator = IfcTesterIdsValidator()
        fake_results = {
            "specifications": [
                {
                    "name": "Passes",
                    "status": True,
                    "requirements": [],
                }
            ]
        }

        issues = validator._map_results(fake_results)
        self.assertEqual(len(issues), 0)

    def test_map_results_handles_empty_specifications(self) -> None:
        from aerobim.infrastructure.adapters.ifc_tester_ids_validator import IfcTesterIdsValidator

        validator = IfcTesterIdsValidator()
        issues = validator._map_results({"specifications": []})
        self.assertEqual(len(issues), 0)

    def test_map_results_multiple_failed_entities(self) -> None:
        from aerobim.infrastructure.adapters.ifc_tester_ids_validator import IfcTesterIdsValidator

        validator = IfcTesterIdsValidator()
        fake_results = {
            "specifications": [
                {
                    "name": "Window Check",
                    "status": False,
                    "requirements": [
                        {
                            "facet_type": "Attribute",
                            "description": "Name must match pattern",
                            "status": False,
                            "failed_entities": [
                                {"element": "GUID-A#1", "reason": "Missing attribute"},
                                {"element": "GUID-B#2", "reason": "Wrong value"},
                            ],
                        }
                    ],
                }
            ]
        }

        issues = validator._map_results(fake_results)
        self.assertEqual(len(issues), 2)
        guids = {i.element_guid for i in issues}
        self.assertEqual(guids, {"GUID-A", "GUID-B"})


if __name__ == "__main__":
    unittest.main()
