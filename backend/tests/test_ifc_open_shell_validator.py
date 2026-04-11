from __future__ import annotations

import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from aerobim.domain.models import ParsedRequirement
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
    ):
        pset_calls: dict[int, int] = {}

        def get_psets(element: _FakeElement) -> dict[str, dict[str, object]]:
            element_id = element.id()
            pset_calls[element_id] = pset_calls.get(element_id, 0) + 1
            return psets_by_element_id[element_id]

        ifcopenshell_module = types.ModuleType("ifcopenshell")
        ifcopenshell_module.open = lambda _path: model

        util_module = types.ModuleType("ifcopenshell.util")
        element_module = types.ModuleType("ifcopenshell.util.element")
        element_module.get_psets = get_psets

        patched_modules = {
            "ifcopenshell": ifcopenshell_module,
            "ifcopenshell.util": util_module,
            "ifcopenshell.util.element": element_module,
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


if __name__ == "__main__":
    unittest.main()
