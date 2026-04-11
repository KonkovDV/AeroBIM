from __future__ import annotations

import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from aerobim.domain.models import ComparisonOperator, ParsedRequirement
from aerobim.infrastructure.adapters.ifc_open_shell_validator import IfcOpenShellValidator


class _FakeElement:
    def __init__(self, element_id: int, guid: str, name: str) -> None:
        self._element_id = element_id
        self.GlobalId = guid
        self.Name = name

    def id(self) -> int:
        return self._element_id


class _FakeModel:
    def __init__(self, elements_by_type: dict[str, list[_FakeElement]]) -> None:
        self._elements_by_type = {
            key.upper(): list(value) for key, value in elements_by_type.items()
        }
        self.by_type_calls: list[str] = []

    def by_type(self, entity_name: str):
        self.by_type_calls.append(entity_name)
        return list(self._elements_by_type.get(entity_name.upper(), []))


class _CountingTargetRefValidator(IfcOpenShellValidator):
    def __init__(self) -> None:
        super().__init__()
        self.target_ref_checks = 0

    def _matches_target_ref(self, element, target_ref: str) -> bool:
        self.target_ref_checks += 1
        return super()._matches_target_ref(element, target_ref)


class IfcOpenShellValidatorCachingTests(unittest.TestCase):
    def _install_fake_ifcopenshell(
        self,
        model: _FakeModel,
        psets_by_element_id: dict[int, dict[str, dict[str, object]]],
        unit_scales: dict[str, float] | None = None,
    ):
        pset_calls: dict[int, int] = {}
        scales = unit_scales or {
            "LENGTHUNIT": 1.0,
            "AREAUNIT": 1.0,
            "VOLUMEUNIT": 1.0,
        }

        def get_psets(element: _FakeElement) -> dict[str, dict[str, object]]:
            element_id = element.id()
            pset_calls[element_id] = pset_calls.get(element_id, 0) + 1
            return psets_by_element_id[element_id]

        ifcopenshell_module = types.ModuleType("ifcopenshell")
        ifcopenshell_module.open = lambda _path: model

        util_module = types.ModuleType("ifcopenshell.util")
        element_module = types.ModuleType("ifcopenshell.util.element")
        element_module.get_psets = get_psets

        unit_module = types.ModuleType("ifcopenshell.util.unit")
        unit_module.calculate_unit_scale = lambda _model, unit_type="LENGTHUNIT": scales.get(
            unit_type, 1.0
        )

        patched_modules = {
            "ifcopenshell": ifcopenshell_module,
            "ifcopenshell.util": util_module,
            "ifcopenshell.util.element": element_module,
            "ifcopenshell.util.unit": unit_module,
        }
        return pset_calls, patch.dict(sys.modules, patched_modules)

    def test_caches_by_type_and_psets_for_repeated_requirements(self) -> None:
        wall = _FakeElement(1, "wall-guid-1", "Wall-01")
        model = _FakeModel({"IFCWALL": [wall]})
        pset_calls, modules_patch = self._install_fake_ifcopenshell(
            model,
            {
                1: {
                    "Pset_WallCommon": {
                        "FireRating": "REI60",
                        "LoadBearing": "True",
                    }
                }
            },
        )
        requirements = [
            ParsedRequirement(
                rule_id="R-1",
                ifc_entity="IFCWALL",
                property_set="Pset_WallCommon",
                property_name="FireRating",
                expected_value="REI60",
            ),
            ParsedRequirement(
                rule_id="R-2",
                ifc_entity="IFCWALL",
                property_set="Pset_WallCommon",
                property_name="LoadBearing",
                expected_value="True",
            ),
        ]

        with tempfile.NamedTemporaryFile(suffix=".ifc") as tmp_file, modules_patch:
            issues = IfcOpenShellValidator().validate(Path(tmp_file.name), requirements)

        self.assertEqual(issues, [])
        self.assertEqual(model.by_type_calls, ["IFCWALL"])
        self.assertEqual(pset_calls, {1: 1})

    def test_caches_target_ref_filter_for_repeated_targeted_requirements(self) -> None:
        wall_1 = _FakeElement(1, "wall-guid-1", "Wall-01")
        wall_2 = _FakeElement(2, "wall-guid-2", "Wall-02")
        model = _FakeModel({"IFCWALL": [wall_1, wall_2]})
        pset_calls, modules_patch = self._install_fake_ifcopenshell(
            model,
            {
                1: {
                    "Pset_WallCommon": {
                        "FireRating": "REI60",
                        "AcousticRating": "Rw50",
                    }
                },
                2: {
                    "Pset_WallCommon": {
                        "FireRating": "REI30",
                        "AcousticRating": "Rw40",
                    }
                },
            },
        )
        requirements = [
            ParsedRequirement(
                rule_id="R-1",
                ifc_entity="IFCWALL",
                target_ref="Wall-01",
                property_set="Pset_WallCommon",
                property_name="FireRating",
                expected_value="REI60",
            ),
            ParsedRequirement(
                rule_id="R-2",
                ifc_entity="IFCWALL",
                target_ref="Wall-01",
                property_set="Pset_WallCommon",
                property_name="AcousticRating",
                expected_value="Rw50",
            ),
        ]
        validator = _CountingTargetRefValidator()

        with tempfile.NamedTemporaryFile(suffix=".ifc") as tmp_file, modules_patch:
            issues = validator.validate(Path(tmp_file.name), requirements)

        self.assertEqual(issues, [])
        self.assertEqual(model.by_type_calls, ["IFCWALL"])
        self.assertEqual(validator.target_ref_checks, 2)
        self.assertEqual(pset_calls, {1: 1})


class IfcOpenShellValidatorUnitNormalizationTests(unittest.TestCase):
    """Tests proving that numeric IFC values are normalized to SI before comparison."""

    def _install_fake_ifcopenshell(
        self,
        model: _FakeModel,
        psets_by_element_id: dict[int, dict[str, dict[str, object]]],
        unit_scales: dict[str, float],
    ):
        def get_psets(element: _FakeElement) -> dict[str, dict[str, object]]:
            return psets_by_element_id[element.id()]

        ifcopenshell_module = types.ModuleType("ifcopenshell")
        ifcopenshell_module.open = lambda _path: model

        util_module = types.ModuleType("ifcopenshell.util")
        element_module = types.ModuleType("ifcopenshell.util.element")
        element_module.get_psets = get_psets

        unit_module = types.ModuleType("ifcopenshell.util.unit")
        unit_module.calculate_unit_scale = lambda _model, unit_type="LENGTHUNIT": unit_scales.get(
            unit_type, 1.0
        )

        patched_modules = {
            "ifcopenshell": ifcopenshell_module,
            "ifcopenshell.util": util_module,
            "ifcopenshell.util.element": element_module,
            "ifcopenshell.util.unit": unit_module,
        }
        return patch.dict(sys.modules, patched_modules)

    def test_mm_model_normalizes_observed_to_si(self) -> None:
        """Model stores width in mm; requirement expects metres.

        Without normalization: 200 <= 0.25 → false issue.
        With normalization:    0.2 <= 0.25 → correct pass.
        """
        wall = _FakeElement(1, "g1", "W1")
        model = _FakeModel({"IFCWALL": [wall]})
        modules_patch = self._install_fake_ifcopenshell(
            model,
            {1: {"Qto_WallBaseQuantities": {"Width": 200.0}}},
            unit_scales={"LENGTHUNIT": 0.001, "AREAUNIT": 1e-6, "VOLUMEUNIT": 1e-9},
        )
        requirements = [
            ParsedRequirement(
                rule_id="R-1",
                ifc_entity="IFCWALL",
                property_set="Qto_WallBaseQuantities",
                property_name="Width",
                operator=ComparisonOperator.LESS_OR_EQUAL,
                expected_value="0.25",
                unit="m",
            ),
        ]
        with tempfile.NamedTemporaryFile(suffix=".ifc") as f, modules_patch:
            issues = IfcOpenShellValidator().validate(Path(f.name), requirements)

        self.assertEqual(issues, [], "200 mm = 0.2 m should pass <= 0.25 m")

    def test_imperial_model_catches_false_positive(self) -> None:
        """Model stores area in sq ft; requirement expects m².

        Without normalization: 269.1 >= 30 → false pass.
        With normalization:    25.0 >= 30  → correct failure.
        """
        wall = _FakeElement(1, "g1", "W1")
        model = _FakeModel({"IFCWALL": [wall]})
        modules_patch = self._install_fake_ifcopenshell(
            model,
            {1: {"Qto_SpaceBaseQuantities": {"NetFloorArea": 269.098}}},
            unit_scales={
                "LENGTHUNIT": 0.3048,
                "AREAUNIT": 0.092903,
                "VOLUMEUNIT": 0.028317,
            },
        )
        requirements = [
            ParsedRequirement(
                rule_id="R-1",
                ifc_entity="IFCWALL",
                property_set="Qto_SpaceBaseQuantities",
                property_name="NetFloorArea",
                operator=ComparisonOperator.GREATER_OR_EQUAL,
                expected_value="30",
                unit="m2",
            ),
        ]
        with tempfile.NamedTemporaryFile(suffix=".ifc") as f, modules_patch:
            issues = IfcOpenShellValidator().validate(Path(f.name), requirements)

        self.assertEqual(len(issues), 1, "25 m² < 30 m² should produce a failure")

    def test_string_properties_unaffected_by_unit_scales(self) -> None:
        """Non-numeric properties like FireRating are never scaled."""
        wall = _FakeElement(1, "g1", "W1")
        model = _FakeModel({"IFCWALL": [wall]})
        modules_patch = self._install_fake_ifcopenshell(
            model,
            {1: {"Pset_WallCommon": {"FireRating": "REI60"}}},
            unit_scales={"LENGTHUNIT": 0.001, "AREAUNIT": 1e-6, "VOLUMEUNIT": 1e-9},
        )
        requirements = [
            ParsedRequirement(
                rule_id="R-1",
                ifc_entity="IFCWALL",
                property_set="Pset_WallCommon",
                property_name="FireRating",
                expected_value="REI60",
            ),
        ]
        with tempfile.NamedTemporaryFile(suffix=".ifc") as f, modules_patch:
            issues = IfcOpenShellValidator().validate(Path(f.name), requirements)

        self.assertEqual(issues, [])

    def test_observed_value_reported_in_requirement_unit(self) -> None:
        """When a mismatch fires, observed_value is converted to the requirement's unit.

        Model uses mm; requirement says m.  Raw observed = 200 mm.
        Expected in report: "0.2" (metres), NOT "200.0".
        """
        wall = _FakeElement(1, "g1", "W1")
        model = _FakeModel({"IFCWALL": [wall]})
        modules_patch = self._install_fake_ifcopenshell(
            model,
            {1: {"Qto_WallBaseQuantities": {"Width": 200.0}}},
            unit_scales={"LENGTHUNIT": 0.001, "AREAUNIT": 1e-6, "VOLUMEUNIT": 1e-9},
        )
        requirements = [
            ParsedRequirement(
                rule_id="R-1",
                ifc_entity="IFCWALL",
                property_set="Qto_WallBaseQuantities",
                property_name="Width",
                operator=ComparisonOperator.LESS_OR_EQUAL,
                expected_value="0.15",
                unit="m",
            ),
        ]
        with tempfile.NamedTemporaryFile(suffix=".ifc") as f, modules_patch:
            issues = IfcOpenShellValidator().validate(Path(f.name), requirements)

        self.assertEqual(len(issues), 1)
        self.assertAlmostEqual(float(issues[0].observed_value), 0.2, places=4)


if __name__ == "__main__":
    unittest.main()
