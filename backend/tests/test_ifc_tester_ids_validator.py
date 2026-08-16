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

    def test_string_failed_status_is_not_a_pass(self) -> None:
        from aerobim.infrastructure.adapters.ifc_tester_ids_validator import IfcTesterIdsValidator

        validator = IfcTesterIdsValidator()
        fake_results = {
            "specifications": [
                {
                    "name": "Wall Fire Rating",
                    "status": "failed",
                    "requirements": [
                        {
                            "facet_type": "Property",
                            "description": "must exist",
                            "status": False,
                            "failed_entities": [{"element": "guid-1"}],
                        }
                    ],
                }
            ]
        }
        issues = validator._map_results(fake_results)
        self.assertGreater(len(issues), 0)

    def test_string_false_empty_spec_is_not_a_pass(self) -> None:
        from aerobim.domain.ids_schema_gate import RULE_STATUS_TYPE
        from aerobim.infrastructure.adapters.ifc_tester_ids_validator import IfcTesterIdsValidator

        validator = IfcTesterIdsValidator()
        issues = validator._map_results(
            {
                "specifications": [
                    {
                        "name": "Drift",
                        "status": "false",
                        "requirements": [],
                    }
                ]
            }
        )
        self.assertGreater(len(issues), 0)
        self.assertTrue(any(issue.rule_id == RULE_STATUS_TYPE for issue in issues))
        self.assertTrue(all(issue.severity is Severity.ERROR for issue in issues))

    def test_string_true_empty_spec_is_not_a_pass(self) -> None:
        from aerobim.infrastructure.adapters.ifc_tester_ids_validator import IfcTesterIdsValidator

        validator = IfcTesterIdsValidator()
        issues = validator._map_results(
            {
                "specifications": [
                    {
                        "name": "LooksPassed",
                        "status": "true",
                        "requirements": [],
                    }
                ]
            }
        )
        self.assertGreater(len(issues), 0)

    def test_bool_false_empty_spec_is_not_a_pass(self) -> None:
        from aerobim.infrastructure.adapters.ifc_tester_ids_validator import IfcTesterIdsValidator

        validator = IfcTesterIdsValidator()
        issues = validator._map_results(
            {
                "specifications": [
                    {
                        "name": "FailedEmpty",
                        "status": False,
                        "cardinality": "required",
                        "requirements": [],
                    }
                ]
            }
        )
        self.assertEqual(len(issues), 1)
        self.assertIn("no requirement findings", issues[0].message)

    def test_map_results_missing_requirement_status_is_failure(self) -> None:
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
                            "description": "status omitted",
                            "failed_entities": [],
                        }
                    ],
                }
            ]
        }
        issues = validator._map_results(fake_results)
        self.assertEqual(len(issues), 1)

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

    def test_map_results_prohibited_specification_with_applicability_match(self) -> None:
        from aerobim.infrastructure.adapters.ifc_tester_ids_validator import IfcTesterIdsValidator

        validator = IfcTesterIdsValidator()
        fake_results = {
            "specifications": [
                {
                    "name": "Prohibited Wall",
                    "status": False,
                    "cardinality": "prohibited",
                    "total_applicable": 1,
                    "requirements": [],
                    "applicable_entities": [
                        {
                            "element": "2hJQkZ0zj1XBp0001#1",
                            "global_id": "2hJQkZ0zj1XBp0001",
                        }
                    ],
                }
            ]
        }

        issues = validator._map_results(fake_results)
        self.assertEqual(len(issues), 1)
        self.assertIn("Prohibited", issues[0].message)
        self.assertEqual(issues[0].element_guid, "2hJQkZ0zj1XBp0001")

    def test_map_results_failed_requirement_without_failed_entities(self) -> None:
        from aerobim.infrastructure.adapters.ifc_tester_ids_validator import IfcTesterIdsValidator

        validator = IfcTesterIdsValidator()
        fake_results = {
            "specifications": [
                {
                    "name": "Required Wall Name",
                    "status": False,
                    "cardinality": "required",
                    "total_applicable": 0,
                    "requirements": [
                        {
                            "facet_type": "Attribute",
                            "description": "The Name shall be Waldo",
                            "status": False,
                            "failed_entities": [],
                        }
                    ],
                }
            ]
        }

        issues = validator._map_results(fake_results)
        self.assertEqual(len(issues), 1)
        self.assertIn("Waldo", issues[0].message)


class IfcTesterIdsValidatorBsiRegressionTests(unittest.TestCase):
    """BSI TestCases that must map to pass/fail consistently with filename prefix."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = Path(__file__).resolve().parents[2]
        cls.bsi_root = cls.repo / "samples" / "ids" / "buildingsmart-testcases" / "cases"

    def _validate(self, case_dir: str, case_id: str) -> bool:
        from aerobim.infrastructure.adapters.ifc_tester_ids_validator import IfcTesterIdsValidator

        case_path = self.bsi_root / case_dir
        issues = IfcTesterIdsValidator().validate(
            case_path / f"{case_id}.ids",
            case_path / f"{case_id}.ifc",
        )
        return len(issues) == 0

    def test_bsi_0093_prohibited_specification_fails(self) -> None:
        case_id = "fail-prohibited_specifications_fails_if_the_applicability_matches"
        self.assertFalse(self._validate("0093", case_id))

    def test_bsi_0094_required_spec_with_no_applicable_entity_fails(self) -> None:
        case_id = "fail-required_specifications_need_at_least_one_applicable_entity_2_2"
        self.assertFalse(self._validate("0094", case_id))


if __name__ == "__main__":
    unittest.main()
