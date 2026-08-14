"""Fail-closed IDS ifcVersion / SKIPPED gate (brief 0.4)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.application.services.capability_matrix import build_report_capabilities
from aerobim.application.services.capability_policy import build_signoff_policy
from aerobim.domain.ids_schema_gate import (
    RULE_IFC_VERSION,
    RULE_SKIPPED,
    collect_schema_mismatches,
    model_schema_allowed,
    parse_ids_specification_versions,
    parse_ifc_file_name,
    parse_ifc_file_schema,
    skipped_spec_fail_closed_rule_id,
)
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    FindingCategory,
    ReportCapabilities,
    Severity,
    ValidationIssue,
)
from aerobim.infrastructure.adapters.ifc_tester_ids_validator import IfcTesterIdsValidator

REPO = Path(__file__).resolve().parents[2]
CASE_0101 = (
    REPO
    / "samples"
    / "ids"
    / "buildingsmart-testcases"
    / "cases"
    / "0101"
    / "pass-specification_version_is_purely_metadata_and_does_not_impact_pass_or_fail_result"
)
WALL_IFC = REPO / "samples" / "ifc" / "wall-pset-qto-pass.ifc"
DIVERGENCES = (
    REPO / "samples" / "ids" / "buildingsmart-testcases" / "AEROBIM_FAIL_CLOSED_DIVERGENCES.json"
)

_IFC2X3_ONLY_IDS = """<?xml version='1.0' encoding='utf-8'?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
    <info><title>IFC2X3-only wall fire rating</title></info>
    <specifications>
        <specification name="Wall Fire Rating IFC2X3" ifcVersion="IFC2X3">
            <applicability minOccurs="0" maxOccurs="unbounded">
                <entity><name><simpleValue>IFCWALL</simpleValue></name></entity>
            </applicability>
            <requirements>
                <property cardinality="required">
                    <propertySet><simpleValue>Pset_WallCommon</simpleValue></propertySet>
                    <baseName><simpleValue>FireRating</simpleValue></baseName>
                    <value><simpleValue>REI60</simpleValue></value>
                </property>
            </requirements>
        </specification>
    </specifications>
</ids>
"""


def _pilot_ok_caps(**overrides: CapabilityStatus) -> ReportCapabilities:
    fields = {
        "clash": CapabilityStatus(CapabilityState.OK),
        "ifc_schema": CapabilityStatus(CapabilityState.OK),
        "mep_system_clash": CapabilityStatus(CapabilityState.OK),
        "unit_scale": CapabilityStatus(CapabilityState.OK),
        "calculation_match": CapabilityStatus(CapabilityState.OK),
        "quantity": CapabilityStatus(CapabilityState.OK),
        "ids": CapabilityStatus(CapabilityState.OK),
    }
    fields.update(overrides)
    return ReportCapabilities(**fields)


class IdsSchemaGateDomainTests(unittest.TestCase):
    def test_parse_file_schema_ifc4(self) -> None:
        header = "ISO-10303-21;\nHEADER;\nFILE_SCHEMA(('IFC4'));\n"
        self.assertEqual(parse_ifc_file_schema(header), "IFC4")

    def test_parse_file_name_originating_system(self) -> None:
        header = WALL_IFC.read_text(encoding="utf-8")
        parsed = parse_ifc_file_name(header)
        assert parsed is not None
        self.assertTrue(parsed.originating_system)

    def test_parse_renga_view_definition_allows_space(self) -> None:
        from aerobim.domain.ids_schema_gate import parse_ifc_view_definition

        header = "FILE_DESCRIPTION(('ViewDefinition [Renga View]'),'2;1');\n"
        self.assertEqual(parse_ifc_view_definition(header), "Renga View")

    def test_ifc2x3_ids_does_not_allow_ifc4_model(self) -> None:
        self.assertFalse(model_schema_allowed("IFC4", frozenset({"IFC2X3"})))
        self.assertTrue(model_schema_allowed("IFC4", frozenset({"IFC2X3", "IFC4"})))

    def test_ifc4x3_is_not_aliased_to_ifc4x3_add2(self) -> None:
        """Exact token match. Fixture FILE_SCHEMA is IFC4X3; IDS lists IFC4X3_ADD2.

        Do not silently treat ADD2 as the same family — that would hide a real
        token gap the same way IfcTester hides ifcVersion.
        """
        self.assertFalse(model_schema_allowed("IFC4X3", frozenset({"IFC4X3_ADD2"})))
        self.assertTrue(model_schema_allowed("IFC4X3_ADD2", frozenset({"IFC4X3_ADD2"})))

    def test_moexp_ifc4_ids_does_not_allow_ifc4x3_renga_export(self) -> None:
        """Official MOEXP IDS is ifcVersion=IFC4. Renga IFC4X3 must fail-close."""
        self.assertFalse(model_schema_allowed("IFC4X3", frozenset({"IFC4"})))
        self.assertFalse(model_schema_allowed("IFC4X3_ADD2", frozenset({"IFC4"})))
        self.assertTrue(model_schema_allowed("IFC4", frozenset({"IFC4"})))

    def test_parse_specification_versions(self) -> None:
        specs = parse_ids_specification_versions(_IFC2X3_ONLY_IDS)
        self.assertEqual(len(specs), 1)
        self.assertEqual(specs[0].name, "Wall Fire Rating IFC2X3")
        self.assertEqual(specs[0].versions, frozenset({"IFC2X3"}))

    def test_parses_namespaced_moexp_specification_ifc4(self) -> None:
        """Official MOEXP IDS uses <ids:specification ifcVersion='IFC4'>."""
        snippet = (
            '<ids:ids xmlns:ids="http://standards.buildingsmart.org/IDS">'
            '<ids:specification ifcVersion="IFC4" name="АР стены">'
            "</ids:specification></ids:ids>"
        )
        specs = parse_ids_specification_versions(snippet)
        self.assertEqual(len(specs), 1)
        self.assertEqual(specs[0].name, "АР стены")
        self.assertEqual(specs[0].versions, frozenset({"IFC4"}))
        self.assertFalse(model_schema_allowed("IFC4X3", specs[0].versions))

    def test_official_moexp_ar_ids_is_ifc4_only(self) -> None:
        ids_path = (
            REPO
            / "samples"
            / "ids"
            / "moexp"
            / "pack"
            / "oks"
            / "IDS_v1.0_Требования_МОГЭ_к_ЦИМ_АР_v3.2.ids"
        )
        specs = parse_ids_specification_versions(ids_path.read_text(encoding="utf-8"))
        self.assertGreater(len(specs), 10)
        self.assertTrue(all(spec.versions == frozenset({"IFC4"}) for spec in specs))

    def test_collect_mismatch_on_wall_fixture_header(self) -> None:
        header = WALL_IFC.read_text(encoding="utf-8")
        schema = parse_ifc_file_schema(header)
        specs = parse_ids_specification_versions(_IFC2X3_ONLY_IDS)
        mismatches = collect_schema_mismatches(model_schema=schema, specs=specs)
        self.assertEqual(len(mismatches), 1)
        self.assertEqual(mismatches[0].model_schema, "IFC4")

    def test_skipped_and_none_status_are_fail_closed(self) -> None:
        self.assertEqual(
            skipped_spec_fail_closed_rule_id(is_ifc_version=False, status=True),
            RULE_IFC_VERSION,
        )
        self.assertEqual(
            skipped_spec_fail_closed_rule_id(status=None, is_skipped=False),
            RULE_SKIPPED,
        )
        self.assertEqual(
            skipped_spec_fail_closed_rule_id(is_skipped=True, status=True),
            RULE_SKIPPED,
        )
        self.assertIsNone(
            skipped_spec_fail_closed_rule_id(is_skipped=False, status=True, is_ifc_version=True)
        )


class IdsFailClosedMappingTests(unittest.TestCase):
    def test_map_results_optional_skip_is_error(self) -> None:
        validator = IfcTesterIdsValidator()
        issues = validator._map_results(
            {
                "specifications": [
                    {
                        "name": "Optional skipped",
                        "status": True,
                        "is_skipped": True,
                        "is_ifc_version": True,
                        "requirements": [],
                    }
                ]
            }
        )
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, RULE_SKIPPED)
        self.assertIs(issues[0].severity, Severity.ERROR)

    def test_map_results_none_status_is_error(self) -> None:
        validator = IfcTesterIdsValidator()
        issues = validator._map_results(
            {
                "specifications": [
                    {
                        "name": "Never ran",
                        "status": None,
                        "is_skipped": False,
                        "is_ifc_version": True,
                        "requirements": [],
                    }
                ]
            }
        )
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, RULE_SKIPPED)

    def test_passing_spec_without_skip_stays_empty(self) -> None:
        validator = IfcTesterIdsValidator()
        issues = validator._map_results(
            {
                "specifications": [
                    {
                        "name": "Passes",
                        "status": True,
                        "is_skipped": False,
                        "is_ifc_version": True,
                        "requirements": [],
                    }
                ]
            }
        )
        self.assertEqual(issues, [])


class IdsFailClosedCapabilityPolicyTests(unittest.TestCase):
    def test_pilot_skipped_ids_requested_blocks_pass(self) -> None:
        caps = _pilot_ok_caps(
            ids=CapabilityStatus(CapabilityState.SKIPPED, "IfcTester skipped specification")
        )
        policy = build_signoff_policy(profile="samolet_pilot")
        self.assertIn("ids", policy.required_capability_blocks_pass(caps))
        self.assertFalse(policy.summary_passed(error_count=0, capabilities=caps))

    def test_pilot_ids_not_requested_does_not_add_ids_block(self) -> None:
        caps = _pilot_ok_caps(
            ids=CapabilityStatus(CapabilityState.SKIPPED, "IDS validation not requested")
        )
        policy = build_signoff_policy(profile="samolet_pilot")
        self.assertNotIn("ids", policy.required_capability_blocks_pass(caps))

    def test_development_skipped_ids_does_not_block(self) -> None:
        caps = _pilot_ok_caps(
            ids=CapabilityStatus(CapabilityState.SKIPPED, "IfcTester skipped specification")
        )
        policy = build_signoff_policy(profile="development")
        self.assertTrue(policy.summary_passed(error_count=0, capabilities=caps))

    def test_ids_capability_failed_on_version_issue(self) -> None:
        caps = build_report_capabilities(
            requirements=(),
            ifc_issues=(),
            ids_path=Path("sample.ids"),
            ids_issues=[
                ValidationIssue(
                    rule_id=RULE_IFC_VERSION,
                    severity=Severity.ERROR,
                    message="version mismatch",
                    category=FindingCategory.IDS_VALIDATION,
                )
            ],
            clash_capability=CapabilityStatus(CapabilityState.SKIPPED, "n/a"),
            drawing_sources=(),
            ids_validator_configured=True,
            ifc_schema_validator_configured=True,
            require_bsi_schema=False,
            raster_analyzer_configured=False,
        )
        self.assertIs(caps.ids.status, CapabilityState.FAILED)


class IdsFailClosedLiveIfcTesterTests(unittest.TestCase):
    def test_case_0101_emits_version_error(self) -> None:
        ids_path = CASE_0101.with_suffix(".ids")
        ifc_path = CASE_0101.with_suffix(".ifc")
        if not ids_path.is_file() or not ifc_path.is_file():
            self.skipTest("BSI case 0101 not vendored")
        try:
            issues = IfcTesterIdsValidator().validate(ids_path, ifc_path)
        except Exception as exc:  # noqa: BLE001 — ifctester env flake
            message = f"{type(exc).__name__}: {exc}".lower()
            if any(token in message for token in ("ifctester", "ifcopenshell", "urlerror")):
                self.skipTest(str(exc))
            raise
        version_issues = [issue for issue in issues if issue.rule_id == RULE_IFC_VERSION]
        self.assertTrue(version_issues, msg=[issue.rule_id for issue in issues])
        self.assertIn("IFC4", version_issues[0].observed_value or "")

    def test_ifc4_fixture_with_ifc2x3_only_ids_fails_closed(self) -> None:
        if not WALL_IFC.is_file():
            self.skipTest("wall fixture missing")
        with tempfile.TemporaryDirectory() as tmp:
            ids_path = Path(tmp) / "ifc2x3-only.ids"
            ids_path.write_text(_IFC2X3_ONLY_IDS, encoding="utf-8")
            try:
                issues = IfcTesterIdsValidator().validate(ids_path, WALL_IFC)
            except Exception as exc:  # noqa: BLE001
                message = f"{type(exc).__name__}: {exc}".lower()
                if any(token in message for token in ("ifctester", "ifcopenshell", "urlerror")):
                    self.skipTest(str(exc))
                raise
        self.assertTrue(any(issue.rule_id == RULE_IFC_VERSION for issue in issues))


class FailClosedDivergenceRegistryTests(unittest.TestCase):
    def test_registry_lists_case_0101(self) -> None:
        payload = json.loads(DIVERGENCES.read_text(encoding="utf-8"))
        ids = {row["case_id"] for row in payload["divergences"]}
        self.assertIn(
            "pass-specification_version_is_purely_metadata_and_does_not_impact_pass_or_fail_result",
            ids,
        )
        self.assertEqual(len(ids), 6)


class ExportIdsFailClosedGateTests(unittest.TestCase):
    def test_schema_walk_finds_0101(self) -> None:
        from aerobim.tools.export_ids_fail_closed_gate import (
            CASE_0101,
            discover_bsi_pairs,
            schema_gate_row,
        )

        pairs = discover_bsi_pairs(REPO / "samples" / "ids" / "buildingsmart-testcases" / "cases")
        match = next(pair for pair in pairs if pair["case_id"] == CASE_0101)
        row = schema_gate_row(match)
        self.assertGreater(int(row["mismatch_count"]), 0)
        self.assertEqual(row["model_schema"], "IFC4")


if __name__ == "__main__":
    unittest.main()
