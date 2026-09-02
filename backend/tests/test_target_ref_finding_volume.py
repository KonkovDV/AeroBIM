"""Regression: ALL target_ref, GUID Name collision, SIG-01 volume taxonomy."""

from __future__ import annotations

import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from aerobim.application.services.drawing_annotation_validation import (
    DrawingAnnotationValidator,
)
from aerobim.domain.consistency import QuantityClaim
from aerobim.domain.finding_volume import (
    REPORT_PHRASE,
    VOLUME_CLASS_UNRESTRICTED_EQ_SAMPLE,
    classify_message_shape,
    classify_volume_record,
    suppressed_remainder,
    volume_from_findings,
    volume_from_issues,
)
from aerobim.domain.ifc_globalid import (
    is_valid_ifc_global_id,
    spf_entity_first_attr_is_global_id,
    spf_line_rooted_global_id,
)
from aerobim.domain.models import (
    ComparisonOperator,
    DrawingAnnotation,
    ParsedRequirement,
    RequirementSource,
    RuleScope,
    Severity,
    SourceKind,
    ToleranceConfig,
    ValidationIssue,
)
from aerobim.domain.quantity import parse_quantity
from aerobim.domain.target_ref import (
    UNRESTRICTED_MISMATCH_SUPPRESSOR_MARKER,
    element_matches_named_target_ref,
    is_unrestricted_target_ref,
    named_target_ref_cache_key,
    target_ref_matches,
)
from aerobim.infrastructure.adapters.basic_ifc_schema_validator import BasicIfcSchemaValidator
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.ifc_open_shell_validator import IfcOpenShellValidator
from aerobim.infrastructure.adapters.ifc_quantity_consistency_adapter import (
    IfcQuantityConsistencyAdapter,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
IFC_REI60 = REPO_ROOT / "samples" / "ifc" / "wall-fire-rating-rei60.ifc"
FIRE_RULES = REPO_ROOT / "samples" / "requirements" / "samolet-fire-safety-rules.txt"

_SPF_HEADER = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('t.ifc','2026-08-31',('AeroBIM'),('AeroBIM'),'','','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
"""
_SPF_FOOTER = """ENDSEC;
END-ISO-10303-21;
"""

# Two valid compressed GUIDs that differ only by case (HD12-TR-01).
_GUID_MIXED = "0aBcDeFgHiJkLmNoPqRsTu"
_GUID_FLIPPED = _GUID_MIXED.swapcase()


class _FakeElement:
    def __init__(
        self,
        element_id: int,
        guid: str,
        name: str,
        *,
        tag: str = "",
        long_name: str = "",
    ) -> None:
        self._element_id = element_id
        self.GlobalId = guid
        self.Name = name
        self.Tag = tag
        self.LongName = long_name

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


class TargetRefWildcardTests(unittest.TestCase):
    def test_all_star_any_and_empty_are_unrestricted(self) -> None:
        for token in (None, "", "ALL", "all", "*", "ANY", "  All  "):
            self.assertTrue(is_unrestricted_target_ref(token), token)
        self.assertFalse(is_unrestricted_target_ref("Wall-01"))
        self.assertTrue(target_ref_matches("ALL", "Wall-01"))
        self.assertFalse(target_ref_matches("Wall-01", "Wall-02"))
        wall = _FakeElement(1, "guid-1", "Fixture", tag="W-01", long_name="Outer wall")
        self.assertTrue(element_matches_named_target_ref(wall, "w-01"))
        self.assertTrue(element_matches_named_target_ref(wall, "OUTER WALL"))
        self.assertTrue(element_matches_named_target_ref(wall, "ALL"))
        self.assertFalse(element_matches_named_target_ref(wall, "Wall-99"))
        self.assertTrue(element_matches_named_target_ref(wall, ""))
        self.assertTrue(element_matches_named_target_ref(wall, None))

    def test_global_id_match_is_case_sensitive(self) -> None:
        self.assertTrue(is_valid_ifc_global_id(_GUID_MIXED))
        self.assertTrue(is_valid_ifc_global_id(_GUID_FLIPPED))
        self.assertNotEqual(_GUID_MIXED, _GUID_FLIPPED)
        wall = _FakeElement(1, _GUID_MIXED, "Fixture")
        self.assertTrue(element_matches_named_target_ref(wall, _GUID_MIXED))
        self.assertFalse(element_matches_named_target_ref(wall, _GUID_FLIPPED))
        self.assertFalse(element_matches_named_target_ref(wall, _GUID_MIXED.lower()))
        self.assertNotEqual(
            named_target_ref_cache_key(_GUID_MIXED),
            named_target_ref_cache_key(_GUID_FLIPPED),
        )

    def test_named_ref_uses_casefold_not_lower(self) -> None:
        wall = _FakeElement(1, "guid-1", "Straße", tag="W-ß")
        self.assertTrue(element_matches_named_target_ref(wall, "STRASSE"))
        self.assertTrue(element_matches_named_target_ref(wall, "w-ss"))
        self.assertTrue(target_ref_matches("Straße", "STRASSE"))

    def test_samolet_fire_pack_parses_all_as_unrestricted(self) -> None:
        requirements = StructuredRequirementExtractor().extract(
            RequirementSource(path=FIRE_RULES, source_kind=SourceKind.STRUCTURED_TEXT)
        )
        self.assertGreaterEqual(len(requirements), 6)
        for req in requirements:
            self.assertEqual(req.target_ref, "ALL")
            self.assertTrue(is_unrestricted_target_ref(req.target_ref))


class AllTargetRefValidatorTests(unittest.TestCase):
    def _install_fake_ifcopenshell(
        self,
        model: _FakeModel,
        psets_by_element_id: dict[int, dict[str, dict[str, object]]],
    ):
        def get_psets(element: _FakeElement) -> dict[str, dict[str, object]]:
            return psets_by_element_id[element.id()]

        ifcopenshell_module = types.ModuleType("ifcopenshell")
        ifcopenshell_module.open = lambda _path: model
        util_module = types.ModuleType("ifcopenshell.util")
        element_module = types.ModuleType("ifcopenshell.util.element")
        element_module.get_psets = get_psets
        unit_module = types.ModuleType("ifcopenshell.util.unit")
        unit_module.calculate_unit_scale = lambda _model, unit_type="LENGTHUNIT": 1.0
        return patch.dict(
            sys.modules,
            {
                "ifcopenshell": ifcopenshell_module,
                "ifcopenshell.util": util_module,
                "ifcopenshell.util.element": element_module,
                "ifcopenshell.util.unit": unit_module,
            },
        )

    def test_all_does_not_emit_missing_entity_when_walls_exist(self) -> None:
        wall = _FakeElement(1, "wall-guid-1", "Wall-01")
        model = _FakeModel({"IFCWALL": [wall]})
        modules_patch = self._install_fake_ifcopenshell(
            model,
            {1: {"Pset_WallCommon": {"FireRating": "REI60"}}},
        )
        requirement = ParsedRequirement(
            rule_id="REQ-FIRE-001",
            ifc_entity="IFCWALL",
            target_ref="ALL",
            property_set="Pset_WallCommon",
            property_name="FireRating",
            expected_value="REI60",
        )
        with tempfile.NamedTemporaryFile(suffix=".ifc") as tmp_file, modules_patch:
            issues = IfcOpenShellValidator().validate(Path(tmp_file.name), [requirement])
        self.assertEqual(issues, [])
        self.assertFalse(
            any("No elements found for entity IFCWALL" in (i.message or "") for i in issues)
        )

    def test_all_missing_property_is_coverage_not_missing_entity(self) -> None:
        wall = _FakeElement(1, "wall-guid-1", "Wall-01")
        model = _FakeModel({"IFCWALL": [wall]})
        modules_patch = self._install_fake_ifcopenshell(model, {1: {}})
        requirement = ParsedRequirement(
            rule_id="REQ-FIRE-001",
            ifc_entity="IFCWALL",
            target_ref="ALL",
            property_set="Pset_WallCommon",
            property_name="FireRating",
            expected_value="REI60",
        )
        with tempfile.NamedTemporaryFile(suffix=".ifc") as tmp_file, modules_patch:
            issues = IfcOpenShellValidator().validate(Path(tmp_file.name), [requirement])
        self.assertEqual(len(issues), 1)
        self.assertIn("was not found on any", issues[0].message)
        self.assertNotIn("No elements found for entity", issues[0].message)

    def test_named_target_ref_matches_tag_case_insensitively(self) -> None:
        wall_1 = _FakeElement(1, "wall-guid-1", "Fixture A", tag="W-01")
        wall_2 = _FakeElement(2, "wall-guid-2", "Fixture B", tag="W-02")
        model = _FakeModel({"IFCWALL": [wall_1, wall_2]})
        modules_patch = self._install_fake_ifcopenshell(
            model,
            {
                1: {"Pset_WallCommon": {"FireRating": "REI60"}},
                2: {"Pset_WallCommon": {"FireRating": "REI30"}},
            },
        )
        requirement = ParsedRequirement(
            rule_id="R-TAG",
            ifc_entity="IFCWALL",
            target_ref="w-01",
            property_set="Pset_WallCommon",
            property_name="FireRating",
            expected_value="REI60",
        )
        with tempfile.NamedTemporaryFile(suffix=".ifc") as tmp_file, modules_patch:
            issues = IfcOpenShellValidator().validate(Path(tmp_file.name), [requirement])
        self.assertEqual(issues, [])

    def test_named_target_ref_still_filters(self) -> None:
        wall_1 = _FakeElement(1, "wall-guid-1", "Wall-01")
        wall_2 = _FakeElement(2, "wall-guid-2", "Wall-02")
        model = _FakeModel({"IFCWALL": [wall_1, wall_2]})
        modules_patch = self._install_fake_ifcopenshell(
            model,
            {
                1: {"Pset_WallCommon": {"FireRating": "REI60"}},
                2: {"Pset_WallCommon": {"FireRating": "REI30"}},
            },
        )
        requirement = ParsedRequirement(
            rule_id="R-1",
            ifc_entity="IFCWALL",
            target_ref="Wall-01",
            property_set="Pset_WallCommon",
            property_name="FireRating",
            expected_value="REI60",
        )
        with tempfile.NamedTemporaryFile(suffix=".ifc") as tmp_file, modules_patch:
            issues = IfcOpenShellValidator().validate(Path(tmp_file.name), [requirement])
        self.assertEqual(issues, [])

    def test_guid_target_ref_does_not_match_case_variant(self) -> None:
        wall_1 = _FakeElement(1, _GUID_MIXED, "Fixture A")
        wall_2 = _FakeElement(2, _GUID_FLIPPED, "Fixture B")
        model = _FakeModel({"IFCWALL": [wall_1, wall_2]})
        modules_patch = self._install_fake_ifcopenshell(
            model,
            {
                1: {"Pset_WallCommon": {"FireRating": "REI60"}},
                2: {"Pset_WallCommon": {"FireRating": "REI30"}},
            },
        )
        req_mixed = ParsedRequirement(
            rule_id="R-GUID-MIXED",
            ifc_entity="IFCWALL",
            target_ref=_GUID_MIXED,
            property_set="Pset_WallCommon",
            property_name="FireRating",
            expected_value="REI60",
        )
        req_flipped = ParsedRequirement(
            rule_id="R-GUID-FLIPPED",
            ifc_entity="IFCWALL",
            target_ref=_GUID_FLIPPED,
            property_set="Pset_WallCommon",
            property_name="FireRating",
            expected_value="REI60",
        )
        req_folded = ParsedRequirement(
            rule_id="R-GUID-LOWER",
            ifc_entity="IFCWALL",
            target_ref=_GUID_MIXED.lower(),
            property_set="Pset_WallCommon",
            property_name="FireRating",
            expected_value="REI60",
        )
        with tempfile.NamedTemporaryFile(suffix=".ifc") as tmp_file, modules_patch:
            issues = IfcOpenShellValidator().validate(
                Path(tmp_file.name),
                [req_mixed, req_flipped, req_folded],
            )
        self.assertEqual(len(issues), 2)
        by_rule = {issue.rule_id: issue for issue in issues}
        self.assertNotIn("R-GUID-MIXED", by_rule)
        self.assertIn("does not match", by_rule["R-GUID-FLIPPED"].message)
        self.assertEqual(by_rule["R-GUID-FLIPPED"].element_guid, _GUID_FLIPPED)
        self.assertIn("No elements found for entity", by_rule["R-GUID-LOWER"].message)

    def test_exists_all_partial_coverage_is_one_row_not_a_pass(self) -> None:
        wall_1 = _FakeElement(1, "wall-guid-1", "Wall-01")
        wall_2 = _FakeElement(2, "wall-guid-2", "Wall-02")
        model = _FakeModel({"IFCWALL": [wall_1, wall_2]})
        modules_patch = self._install_fake_ifcopenshell(
            model,
            {1: {"Pset_WallCommon": {"FireRating": "REI60"}}, 2: {}},
        )
        requirement = ParsedRequirement(
            rule_id="SAM-AR-018",
            ifc_entity="IFCWALL",
            target_ref="ALL",
            property_set="Pset_WallCommon",
            property_name="FireRating",
            operator=ComparisonOperator.EXISTS,
        )
        with tempfile.NamedTemporaryFile(suffix=".ifc") as tmp_file, modules_patch:
            issues = IfcOpenShellValidator().validate(Path(tmp_file.name), [requirement])
        self.assertEqual(len(issues), 1)
        self.assertIn("is missing on 1 of 2", issues[0].message)

    def test_unrestricted_mismatches_are_capped(self) -> None:
        walls = [_FakeElement(i, f"wall-guid-{i}", f"Wall-{i}") for i in range(1, 4)]
        model = _FakeModel({"IFCWALL": walls})
        modules_patch = self._install_fake_ifcopenshell(
            model,
            {i: {"Pset_WallCommon": {"FireRating": "REI30"}} for i in range(1, 4)},
        )
        requirement = ParsedRequirement(
            rule_id="REQ-FIRE-001",
            ifc_entity="IFCWALL",
            target_ref="ALL",
            property_set="Pset_WallCommon",
            property_name="FireRating",
            expected_value="REI60",
        )
        from aerobim.infrastructure.adapters import ifc_open_shell_validator as validator_mod

        with (
            tempfile.NamedTemporaryFile(suffix=".ifc") as tmp_file,
            modules_patch,
            patch.object(validator_mod, "UNRESTRICTED_ELEMENT_MISMATCH_CAP", 2),
        ):
            issues = IfcOpenShellValidator().validate(Path(tmp_file.name), [requirement])
        mismatch = [i for i in issues if "does not match" in i.message]
        suppressed = [i for i in issues if "suppressed" in i.message]
        self.assertEqual(len(mismatch), 2)
        self.assertEqual(len(suppressed), 1)
        self.assertIn("not a customer defect list", suppressed[0].message)
        self.assertTrue(all("unsigned pack" in item.message for item in mismatch))
        self.assertTrue(all("not a statutory claim" in item.message for item in mismatch))
        self.assertEqual(
            classify_volume_record(
                {
                    "rule_id": "REQ-FIRE-001",
                    "target_ref": "ALL",
                    "element_guid": "wall-guid-1",
                    "message": mismatch[0].message,
                }
            ),
            VOLUME_CLASS_UNRESTRICTED_EQ_SAMPLE,
        )


class DrawingAllTargetRefTests(unittest.TestCase):
    def test_all_matches_any_annotation_of_the_measure(self) -> None:
        requirement = ParsedRequirement(
            rule_id="REQ-DRW-ALL",
            rule_scope=RuleScope.DRAWING_ANNOTATION,
            target_ref="ALL",
            property_name="thickness",
            operator=ComparisonOperator.GREATER_OR_EQUAL,
            expected_value="200",
            unit="mm",
        )
        annotation = DrawingAnnotation(
            annotation_id="ANN-001",
            sheet_id="A-101",
            target_ref="WALL-01",
            measure_name="thickness",
            observed_value="220",
            unit="mm",
            source="raster-drawing-analyzer",
        )
        issues = DrawingAnnotationValidator(ToleranceConfig()).validate(
            (requirement,), (annotation,)
        )
        self.assertEqual(issues, [])

    def test_unrestricted_drawing_mismatches_are_capped(self) -> None:
        requirement = ParsedRequirement(
            rule_id="REQ-DRW-ALL",
            rule_scope=RuleScope.DRAWING_ANNOTATION,
            target_ref="ALL",
            property_name="thickness",
            operator=ComparisonOperator.GREATER_OR_EQUAL,
            expected_value="200",
            unit="mm",
        )
        annotations = tuple(
            DrawingAnnotation(
                annotation_id=f"ANN-{index}",
                sheet_id="A-101",
                target_ref=f"WALL-{index:02d}",
                measure_name="thickness",
                observed_value="100",
                unit="mm",
                source="raster-drawing-analyzer",
            )
            for index in range(1, 4)
        )
        from aerobim.application.services import drawing_annotation_validation as drawing_mod

        with patch.object(drawing_mod, "UNRESTRICTED_ELEMENT_MISMATCH_CAP", 2):
            issues = DrawingAnnotationValidator(ToleranceConfig()).validate(
                (requirement,), annotations
            )
        mismatch = [i for i in issues if "does not match" in i.message]
        suppressed = [i for i in issues if "suppressed" in i.message]
        self.assertEqual(len(mismatch), 2)
        self.assertEqual(len(suppressed), 1)
        self.assertIn("not a customer defect list", suppressed[0].message)


class SpfGuidNameCollisionTests(unittest.TestCase):
    def test_property_and_material_22_char_names_are_not_guids(self) -> None:
        self.assertFalse(spf_entity_first_attr_is_global_id("IFCPROPERTYSINGLEVALUE"))
        self.assertFalse(spf_entity_first_attr_is_global_id("IFCMATERIAL"))
        self.assertTrue(spf_entity_first_attr_is_global_id("IFCWALL"))
        self.assertTrue(spf_entity_first_attr_is_global_id("IFCPROPERTYSET"))
        self.assertTrue(spf_entity_first_attr_is_global_id("IFCRELDEFINESBYPROPERTIES"))
        self.assertTrue(spf_entity_first_attr_is_global_id("IFCWALLSTANDARDCASE"))
        self.assertFalse(spf_entity_first_attr_is_global_id("IFCFOOBAR"))
        self.assertFalse(spf_entity_first_attr_is_global_id("IFCCOSTVALUE"))
        self.assertTrue(spf_entity_first_attr_is_global_id("IFCREINFORCINGBAR"))
        self.assertTrue(spf_entity_first_attr_is_global_id("IFCTENDON"))
        self.assertTrue(spf_entity_first_attr_is_global_id("IFCVOIDINGFEATURE"))
        self.assertTrue(spf_entity_first_attr_is_global_id("IFCMECHANICALFASTENER"))
        self.assertFalse(spf_entity_first_attr_is_global_id("IFCREINFORCEMENTDEFINITIONPROPERTIES"))
        self.assertIsNone(
            spf_line_rooted_global_id(
                "#8=IFCPROPERTYSINGLEVALUE('TreadLengthAtInnerSide',$,IFCLENGTHMEASURE(0.25),$);"
            )
        )
        self.assertIsNone(
            spf_line_rooted_global_id("#10=IFCMATERIAL('Stainless Steel_Weland',$,$);")
        )
        self.assertEqual(
            spf_line_rooted_global_id(
                "#6=IFCWALL('38FRviGan7WhU9JrK165gm',$,'Fixture Wall',$,$,$,$,$,$);"
            ),
            "38FRviGan7WhU9JrK165gm",
        )

    def test_schema_pregate_ignores_repeated_property_names(self) -> None:
        body = (
            _SPF_HEADER
            + "#6=IFCWALL('38FRviGan7WhU9JrK165gm',$,'Wall A',$,$,$,$,$,$);\n"
            + "#7=IFCWALL('39FRviGan7WhU9JrK165gn',$,'Wall B',$,$,$,$,$,$);\n"
            + "#8=IFCPROPERTYSINGLEVALUE('TreadLengthAtInnerSide',$,IFCLENGTHMEASURE(0.25),$);\n"
            + "#9=IFCPROPERTYSINGLEVALUE('TreadLengthAtInnerSide',$,IFCLENGTHMEASURE(0.26),$);\n"
            + "#10=IFCMATERIAL('Stainless Steel_Weland',$,$);\n"
            + "#11=IFCMATERIAL('Stainless Steel_Weland',$,$);\n"
            + _SPF_FOOTER
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "names.ifc"
            path.write_text(body, encoding="utf-8")
            issues = BasicIfcSchemaValidator().validate_schema(path)
        self.assertFalse(any(i.rule_id == "AEROBIM-GUID-DUPLICATE" for i in issues))

    def test_schema_pregate_joins_wrapped_guid_line(self) -> None:
        body = (
            _SPF_HEADER
            + "#6=IFCWALL(\n"
            + "'38FRviGan7WhU9JrK165gm',$,'Wall A',$,$,$,$,$,$);\n"
            + "#7=IFCWALL(\n"
            + "'38FRviGan7WhU9JrK165gm',$,'Wall B',$,$,$,$,$,$);\n"
            + _SPF_FOOTER
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wrap.ifc"
            path.write_text(body, encoding="utf-8")
            issues = BasicIfcSchemaValidator().validate_schema(path)
        duplicates = [i for i in issues if i.rule_id == "AEROBIM-GUID-DUPLICATE"]
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0].element_guid, "38FRviGan7WhU9JrK165gm")

    def test_schema_pregate_ignores_unknown_type_22_char_name(self) -> None:
        body = (
            _SPF_HEADER
            + "#6=IFCWALL('38FRviGan7WhU9JrK165gm',$,'Wall A',$,$,$,$,$,$);\n"
            + "#8=IFCFOOBAR('TreadLengthAtInnerSide',$,$);\n"
            + "#9=IFCFOOBAR('TreadLengthAtInnerSide',$,$);\n"
            + _SPF_FOOTER
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "foo.ifc"
            path.write_text(body, encoding="utf-8")
            issues = BasicIfcSchemaValidator().validate_schema(path)
        self.assertFalse(any(i.rule_id == "AEROBIM-GUID-DUPLICATE" for i in issues))

    def test_schema_pregate_still_flags_duplicate_rooted_guid(self) -> None:
        body = (
            _SPF_HEADER
            + "#6=IFCWALL('38FRviGan7WhU9JrK165gm',$,'Wall A',$,$,$,$,$,$);\n"
            + "#7=IFCWALL('38FRviGan7WhU9JrK165gm',$,'Wall B',$,$,$,$,$,$);\n"
            + _SPF_FOOTER
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dup.ifc"
            path.write_text(body, encoding="utf-8")
            issues = BasicIfcSchemaValidator().validate_schema(path)
        duplicates = [i for i in issues if i.rule_id == "AEROBIM-GUID-DUPLICATE"]
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0].element_guid, "38FRviGan7WhU9JrK165gm")


class FindingVolumeTaxonomyTests(unittest.TestCase):
    def test_classifies_hitl_capability_advisory_and_coverage(self) -> None:
        self.assertEqual(
            classify_volume_record({"rule_id": "AEROBIM-DRAWING-REGION-HITL"}),
            "service_hitl",
        )
        self.assertEqual(
            classify_volume_record({"rule_id": "AEROBIM-CLASH-CAPABILITY"}),
            "service_capability",
        )
        self.assertEqual(
            classify_volume_record({"rule_id": "AEROBIM-SPACE-EFFICIENCY-CANDIDATE"}),
            "advisory_unsigned",
        )
        self.assertEqual(
            classify_volume_record(
                {
                    "rule_id": "REQ-FIRE-001",
                    "message": "No elements found for entity IFCWALL",
                }
            ),
            "entity_presence",
        )
        self.assertEqual(
            classify_volume_record(
                {
                    "rule_id": "REQ-FIRE-001",
                    "message": (
                        "Property Pset_WallCommon.FireRating was not found on any IFCWALL elements"
                    ),
                }
            ),
            "coverage_unsigned",
        )
        self.assertEqual(
            classify_volume_record({"rule_id": "SAM-AR-001"}),
            "coverage_unsigned",
        )
        self.assertEqual(
            classify_volume_record({"rule_id": "SAM-AR-020"}),
            "element_detection_unsigned",
        )
        self.assertEqual(
            classify_volume_record(
                {
                    "rule_id": "REQ-FIRE-001",
                    "element_guid": "wall-guid-1",
                    "message": (
                        "Property Pset_WallCommon.FireRating does not match the expected value"
                    ),
                }
            ),
            VOLUME_CLASS_UNRESTRICTED_EQ_SAMPLE,
        )
        self.assertEqual(
            classify_volume_record(
                {
                    "rule_id": "SAM-AR-020",
                    "element_guid": "rail-1",
                    "message": (
                        "Property Pset_RailingCommon.Height does not match the expected value"
                    ),
                }
            ),
            VOLUME_CLASS_UNRESTRICTED_EQ_SAMPLE,
        )
        self.assertEqual(
            classify_volume_record(
                {
                    "rule_id": "REQ-FIRE-001",
                    "target_ref": "Wall-01",
                    "element_guid": "wall-guid-1",
                    "message": (
                        "Property Pset_WallCommon.FireRating does not match the expected value"
                    ),
                }
            ),
            "element_detection_unsigned",
        )
        self.assertEqual(
            classify_volume_record({"rule_id": "REQ-FIRE-001"}),
            "unsigned_universal_rule",
        )
        self.assertEqual(
            classify_volume_record({"rule_id": "REQ-MEP-001"}),
            "unsigned_universal_rule",
        )
        self.assertEqual(
            classify_volume_record(
                {
                    "rule_id": "SAM-AR-005",
                    "message": (
                        "Property Pset_SpaceCommon.OccupancyType is missing "
                        "on 12 of 16000 IFCSPACE elements"
                    ),
                }
            ),
            "coverage_unsigned",
        )
        self.assertEqual(
            classify_volume_record(
                {
                    "rule_id": "REQ-FIRE-001",
                    "message": (
                        f"12 further IFCWALL property mismatches "
                        f"{UNRESTRICTED_MISMATCH_SUPPRESSOR_MARKER} 50; "
                        "not a customer defect list)"
                    ),
                }
            ),
            "coverage_unsigned",
        )

    def test_volume_table_keeps_raw_total_and_mandated_phrase(self) -> None:
        table = volume_from_findings(
            [
                {"rule_id": "AEROBIM-DRAWING-REGION-HITL", "severity": "info"},
                {"rule_id": "AEROBIM-CLASH-CAPABILITY", "severity": "error"},
                {
                    "rule_id": "SAM-AR-020",
                    "element_guid": "g1",
                    "severity": "error",
                    "category": "ifc-validation",
                },
            ]
        )
        self.assertEqual(table["total"], 3)
        self.assertEqual(table["machine_record_count"], 3)
        self.assertEqual(table["service_record_count"], 2)
        self.assertEqual(table["report_phrase"], REPORT_PHRASE)
        self.assertFalse(table["is_accuracy"])
        self.assertFalse(table["is_pack_processed"])
        self.assertFalse(table["is_customer_defect_list"])
        self.assertEqual(table["by_volume_class"]["service_hitl"], 1)
        self.assertEqual(table["by_volume_class"]["service_capability"], 1)
        self.assertEqual(table["by_volume_class"]["element_detection_unsigned"], 1)
        self.assertEqual(table["publishable_finding_count"], 0)
        self.assertFalse(table["suppressed_remainder_is_finding_count"])
        self.assertIn("Not product accuracy", table["claim_boundary"])
        self.assertIn(REPORT_PHRASE, table["claim_boundary"])
        self.assertEqual(
            classify_message_shape(
                "Property Pset_WallCommon.FireRating does not match the expected value"
            ),
            "property_mismatch",
        )
        self.assertEqual(
            suppressed_remainder(
                "12 further IFCWALL property mismatches "
                f"{UNRESTRICTED_MISMATCH_SUPPRESSOR_MARKER} 50; "
                "not a customer defect list)"
            ),
            12,
        )

    def test_volume_from_issues_reads_validation_issue(self) -> None:
        table = volume_from_issues(
            [
                ValidationIssue(
                    rule_id="AEROBIM-DRAWING-REGION-HITL",
                    severity=Severity.INFO,
                    message="region",
                )
            ]
        )
        self.assertEqual(table["total"], 1)
        self.assertEqual(table["by_volume_class"]["service_hitl"], 1)
        self.assertFalse(table["is_accuracy"])

    def test_all_eq_cap_samples_are_not_element_detections(self) -> None:
        table = volume_from_findings(
            [
                {
                    "rule_id": "REQ-FIRE-001",
                    "element_guid": "g1",
                    "message": (
                        "Property Pset_WallCommon.FireRating does not match the expected value"
                    ),
                    "severity": "error",
                    "category": "ifc-validation",
                },
                {
                    "rule_id": "SAM-AR-011",
                    "message": (
                        "Property Pset_WallCommon.FireRating "
                        "is missing on 10 of 12 IFCWALL elements"
                    ),
                    "severity": "error",
                    "category": "ifc-validation",
                },
                {
                    "rule_id": "REQ-FIRE-001",
                    "message": (
                        f"12 further IFCWALL property mismatches "
                        f"{UNRESTRICTED_MISMATCH_SUPPRESSOR_MARKER} 50; "
                        "not a customer defect list)"
                    ),
                    "severity": "error",
                },
            ]
        )
        self.assertEqual(table["by_volume_class"][VOLUME_CLASS_UNRESTRICTED_EQ_SAMPLE], 1)
        self.assertEqual(table["by_volume_class"]["coverage_unsigned"], 2)
        self.assertNotIn("element_detection_unsigned", table["by_volume_class"])
        self.assertEqual(table["capped_eq_sample_count"], 1)
        self.assertEqual(table["suppressed_remainder_sum"], 12)
        self.assertFalse(table["suppressed_remainder_is_finding_count"])
        self.assertGreaterEqual(table["overlap_unsigned_group_count"], 1)
        self.assertEqual(table["publishable_finding_count"], 0)
        self.assertEqual(table["by_message_shape"]["property_mismatch"], 1)
        self.assertEqual(table["by_message_shape"]["mismatch_suppressed"], 1)


class QuantityAllTargetRefTests(unittest.TestCase):
    def test_all_does_not_pass_on_the_first_matching_space(self) -> None:
        spaces = [_FakeElement(1, "s-1", "A101"), _FakeElement(2, "s-2", "A102")]
        model = _FakeModel({"IFCSPACE": spaces})

        def get_psets(element: _FakeElement) -> dict[str, dict[str, object]]:
            areas = {1: 100.0, 2: 50.0}
            return {"Qto_SpaceBaseQuantities": {"NetFloorArea": areas[element.id()]}}

        claim = QuantityClaim(
            claim_id="Q-1",
            target_ref="ALL",
            ifc_entity="IFCSPACE",
            quantity_name="NetFloorArea",
            declared=parse_quantity(100.0, "m2"),
        )
        with (
            tempfile.NamedTemporaryFile(suffix=".ifc") as tmp_file,
            patch("ifcopenshell.util.element.get_psets", get_psets),
            patch(
                "aerobim.infrastructure.adapters.ifc_file_open.open_ifc_session",
                return_value=types.SimpleNamespace(model=model),
            ),
        ):
            issues = IfcQuantityConsistencyAdapter().check(Path(tmp_file.name), [claim])
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, "AEROBIM-QTY-MISMATCH")
        self.assertIn("1 of 2", issues[0].message)

    def test_named_quantity_matches_tag_case_insensitively(self) -> None:
        space = _FakeElement(1, "s-1", "Room", tag="A101")
        model = _FakeModel({"IFCSPACE": [space]})

        def get_psets(element: _FakeElement) -> dict[str, dict[str, object]]:
            return {"Qto_SpaceBaseQuantities": {"NetFloorArea": 12.5}}

        claim = QuantityClaim(
            claim_id="Q-2",
            target_ref="a101",
            ifc_entity="IFCSPACE",
            quantity_name="NetFloorArea",
            declared=parse_quantity(12.5, "m2"),
        )
        with (
            tempfile.NamedTemporaryFile(suffix=".ifc") as tmp_file,
            patch("ifcopenshell.util.element.get_psets", get_psets),
            patch(
                "aerobim.infrastructure.adapters.ifc_file_open.open_ifc_session",
                return_value=types.SimpleNamespace(model=model),
            ),
        ):
            issues = IfcQuantityConsistencyAdapter().check(Path(tmp_file.name), [claim])
        self.assertEqual(issues, [])


class ReI60FireAllIntegrationTests(unittest.TestCase):
    def test_unsigned_fire_all_sees_the_fixture_wall(self) -> None:
        if not IFC_REI60.exists():
            raise unittest.SkipTest("rei60 fixture missing")
        requirements = StructuredRequirementExtractor().extract(
            RequirementSource(path=FIRE_RULES, source_kind=SourceKind.STRUCTURED_TEXT)
        )
        wall_rule = next(item for item in requirements if item.rule_id == "REQ-FIRE-001")
        issues = IfcOpenShellValidator().validate(IFC_REI60, [wall_rule])
        self.assertFalse(
            any("No elements found for entity IFCWALL" in (i.message or "") for i in issues)
        )


if __name__ == "__main__":
    unittest.main()
