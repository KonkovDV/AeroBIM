"""IDS version gate maps pre-final IFC4x3 headers to IFC4X3_ADD2 with a warning."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.domain.ids_schema_gate import (
    RULE_IFC_VERSION,
    RULE_IFC_VERSION_PREFINAL,
    collect_pre_final_mappings,
    collect_schema_mismatches,
    ids_validation_schema,
    model_schema_allowed,
    parse_ids_specification_versions,
)
from aerobim.domain.models import Severity

REPO = Path(__file__).resolve().parents[2]
IFC4X3_WALL = REPO / "samples" / "ifc" / "wall-pset-ifc4x3.ifc"
PRE_FINAL = ("IFC4X3", "IFC4X3_ADD1", "IFC4X3_TC1")


def _ids(versions: str) -> str:
    return f"""<?xml version='1.0' encoding='utf-8'?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
    <info><title>pre-final mapping</title></info>
    <specifications>
        <specification name="Wall exists" ifcVersion="{versions}">
            <applicability minOccurs="1" maxOccurs="unbounded">
                <entity><name><simpleValue>IFCWALL</simpleValue></name></entity>
            </applicability>
            <requirements>
                <attribute><name><simpleValue>Name</simpleValue></name></attribute>
            </requirements>
        </specification>
    </specifications>
</ids>
"""


def _kernel_has_add2_only() -> bool:
    try:
        import ifcopenshell
    except ModuleNotFoundError:
        return False
    return not str(getattr(ifcopenshell, "version", "0.8")).startswith("0.8")


class DomainMappingTests(unittest.TestCase):
    def test_validation_schema_maps_each_pre_final_variant(self) -> None:
        for token in PRE_FINAL:
            with self.subTest(token=token):
                self.assertEqual(ids_validation_schema(token), "IFC4X3_ADD2")

    def test_final_and_other_schemas_unchanged(self) -> None:
        for token in ("IFC4X3_ADD2", "IFC4", "IFC2X3", "IFC5", None):
            with self.subTest(token=token):
                self.assertEqual(ids_validation_schema(token), token)

    def test_strict_primitive_stays_exact(self) -> None:
        self.assertFalse(model_schema_allowed("IFC4X3", frozenset({"IFC4X3_ADD2"})))

    def test_add2_spec_gets_mapping_not_mismatch(self) -> None:
        specs = parse_ids_specification_versions(_ids("IFC4X3_ADD2"))
        for token in PRE_FINAL:
            with self.subTest(token=token):
                mismatches = collect_schema_mismatches(
                    model_schema=ids_validation_schema(token), specs=specs
                )
                mappings = collect_pre_final_mappings(model_schema=token, specs=specs)
                self.assertEqual(mismatches, ())
                self.assertEqual(len(mappings), 1)
                self.assertEqual(mappings[0].header_schema, token)
                self.assertEqual(mappings[0].validated_schema, "IFC4X3_ADD2")

    def test_ifc4_only_spec_still_mismatches_and_gets_no_mapping(self) -> None:
        specs = parse_ids_specification_versions(_ids("IFC4"))
        mismatches = collect_schema_mismatches(
            model_schema=ids_validation_schema("IFC4X3_TC1"), specs=specs
        )
        self.assertEqual(len(mismatches), 1)
        self.assertEqual(collect_pre_final_mappings(model_schema="IFC4X3_TC1", specs=specs), ())

    def test_final_header_gets_no_mapping(self) -> None:
        specs = parse_ids_specification_versions(_ids("IFC4X3_ADD2"))
        self.assertEqual(collect_pre_final_mappings(model_schema="IFC4X3_ADD2", specs=specs), ())


@unittest.skipUnless(_kernel_has_add2_only(), "needs the IfcOpenShell 0.9 kernel")
class ValidatorIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        from aerobim.infrastructure.adapters.ifc_file_open import (
            reset_ifc_parse_cache_for_tests,
        )

        reset_ifc_parse_cache_for_tests()
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(reset_ifc_parse_cache_for_tests)

    def _run(self, header_token: str, versions: str):
        from aerobim.infrastructure.adapters.ifc_tester_ids_validator import (
            IfcTesterIdsValidator,
        )

        root = Path(self._tmp.name)
        text = IFC4X3_WALL.read_text(encoding="utf-8").replace(
            "FILE_SCHEMA(('IFC4X3_ADD2'))", f"FILE_SCHEMA(('{header_token}'))"
        )
        ifc = root / f"{header_token}-{versions.replace(' ', '_')}.ifc"
        ifc.write_text(text, encoding="utf-8")
        ids = root / "spec.ids"
        ids.write_text(_ids(versions), encoding="utf-8")
        return IfcTesterIdsValidator().validate(ids, ifc)

    def test_each_variant_warns_and_has_no_version_error(self) -> None:
        for token in PRE_FINAL:
            with self.subTest(token=token):
                issues = self._run(token, "IFC4X3_ADD2")
                self.assertFalse([i for i in issues if i.rule_id == RULE_IFC_VERSION])
                warnings = [i for i in issues if i.rule_id == RULE_IFC_VERSION_PREFINAL]
                self.assertEqual(len(warnings), 1)
                self.assertIs(warnings[0].severity, Severity.WARNING)
                self.assertIn(token, warnings[0].message)
                self.assertIn("IFC4X3_ADD2", warnings[0].message)
                self.assertIn("Wall exists", warnings[0].message)
                self.assertEqual(warnings[0].observed_value, token)
                self.assertEqual(warnings[0].expected_value, "IFC4X3_ADD2")
                self.assertFalse([i for i in issues if i.severity is Severity.ERROR])

    def test_ifc4_only_ids_still_errors_and_names_both_schemas(self) -> None:
        issues = self._run("IFC4X3_ADD1", "IFC4")
        errors = [i for i in issues if i.rule_id == RULE_IFC_VERSION]
        self.assertEqual(len(errors), 1)
        self.assertIn("IFC4X3_ADD1 (read as IFC4X3_ADD2)", errors[0].observed_value or "")
        self.assertFalse([i for i in issues if i.rule_id == RULE_IFC_VERSION_PREFINAL])

    def test_final_header_has_no_warning(self) -> None:
        issues = self._run("IFC4X3_ADD2", "IFC4X3_ADD2")
        self.assertFalse([i for i in issues if i.rule_id == RULE_IFC_VERSION_PREFINAL])
        self.assertFalse([i for i in issues if i.severity is Severity.ERROR])


if __name__ == "__main__":
    unittest.main()
