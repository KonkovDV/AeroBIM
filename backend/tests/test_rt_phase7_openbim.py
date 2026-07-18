"""Phase 7 openBIM correctness: schema honesty, IDS facets, GlobalId, BCF XSD, cross-doc."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.ifc_globalid import (
    collect_global_id_integrity_issues,
    is_valid_ifc_global_id,
)
from aerobim.domain.models import (
    CapabilityState,
    ParsedRequirement,
    RequirementSource,
    SourceKind,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.basic_ifc_schema_validator import BasicIfcSchemaValidator
from aerobim.infrastructure.adapters.bcf_consumers import verify_bcf_zip_structure
from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
from aerobim.infrastructure.adapters.structured_drawing_analyzer import StructuredDrawingAnalyzer
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator
from aerobim.infrastructure.adapters.xml_ids_document_auditor import XmlIdsDocumentAuditor


_MINIMAL_SPF = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('t.ifc','2026-07-18',('AeroBIM'),('AeroBIM'),'','','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
ENDSEC;
END-ISO-10303-21;
"""

_UNSUPPORTED_SPF = _MINIMAL_SPF.replace("IFC4", "IFC99_FAKE")


def _minimal_uc(**kwargs: object) -> AnalyzeProjectPackageUseCase:
    base: dict[str, object] = {
        "requirement_extractor": StructuredRequirementExtractor(),
        "narrative_rule_synthesizer": NarrativeRuleSynthesizer(),
        "drawing_analyzer": StructuredDrawingAnalyzer(),
        "ifc_validator": MagicMock(validate=MagicMock(return_value=[])),
        "remark_generator": TemplateRemarkGenerator(),
        "audit_report_store": InMemoryAuditStore(),
    }
    base.update(kwargs)
    return AnalyzeProjectPackageUseCase(**base)  # type: ignore[arg-type]


class Phase7SchemaHonestyTests(unittest.TestCase):
    def test_unsupported_file_schema_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.ifc"
            path.write_text(_UNSUPPORTED_SPF, encoding="utf-8")
            issues = BasicIfcSchemaValidator().validate_schema(path)
        self.assertTrue(any(i.rule_id == "AEROBIM-IFC-SCHEMA-UNSUPPORTED" for i in issues))

    def test_spf_only_under_require_bsi_is_not_verified(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            ifc = Path(temporary_directory) / "m.ifc"
            ifc.write_text(_MINIMAL_SPF, encoding="utf-8")
            uc = _minimal_uc(
                require_bsi_schema=True,
                ifc_schema_validator=BasicIfcSchemaValidator(),
                require_mep_system_clash=False,
            )
            report = uc.execute(
                ValidationRequest(
                    request_id="p7-schema",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                )
            )
        assert report.capabilities is not None
        self.assertEqual(report.capabilities.ifc_schema.status, CapabilityState.NOT_VERIFIED)
        self.assertFalse(report.summary.passed)


class Phase7IdsFacetTests(unittest.TestCase):
    def test_unsupported_facet_fail_closed(self) -> None:
        ids_xml = """<?xml version="1.0"?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
  <info><title>t</title></info>
  <specifications>
    <specification name="s" ifcVersion="IFC4">
      <applicability>
        <entity><name><simpleValue>IFCWALL</simpleValue></name></entity>
        <unknownFacet><simpleValue>x</simpleValue></unknownFacet>
      </applicability>
      <requirements>
        <property>
          <propertySet><simpleValue>Pset_WallCommon</simpleValue></propertySet>
          <baseName><simpleValue>FireRating</simpleValue></baseName>
        </property>
      </requirements>
    </specification>
  </specifications>
</ids>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.ids"
            path.write_text(ids_xml, encoding="utf-8")
            issues = XmlIdsDocumentAuditor().audit(path)
        self.assertTrue(any(i.rule_id == "AEROBIM-IDS-UNSUPPORTED-FACET" for i in issues))

    def test_empty_applicability_fail_closed(self) -> None:
        ids_xml = """<?xml version="1.0"?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
  <info><title>t</title></info>
  <specifications>
    <specification name="s" ifcVersion="IFC4">
      <applicability></applicability>
      <requirements>
        <entity><name><simpleValue>IFCWALL</simpleValue></name></entity>
      </requirements>
    </specification>
  </specifications>
</ids>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.ids"
            path.write_text(ids_xml, encoding="utf-8")
            issues = XmlIdsDocumentAuditor().audit(path)
        self.assertTrue(any(i.rule_id == "AEROBIM-IDS-EMPTY-APPLICABILITY" for i in issues))


class Phase7GlobalIdTests(unittest.TestCase):
    def test_valid_guid_shape(self) -> None:
        self.assertTrue(is_valid_ifc_global_id("0$vis3Zjr9Qe8$3$abcABC"))
        self.assertFalse(is_valid_ifc_global_id("short"))
        self.assertFalse(is_valid_ifc_global_id("!!!!!!!!!!!!!!!!!!!!!!"))

    def test_duplicate_and_invalid_emit_errors(self) -> None:
        class _El:
            def __init__(self, guid: str) -> None:
                self.GlobalId = guid

        good = "0123456789ABCDEFGHIJ_$"
        issues = collect_global_id_integrity_issues(
            [_El(good), _El(good), _El("bad"), _El("")]
        )
        rule_ids = {i.rule_id for i in issues}
        self.assertIn("AEROBIM-IFC-GUID-DUPLICATE", rule_ids)
        self.assertIn("AEROBIM-IFC-GUID-INVALID", rule_ids)


class Phase7CrossDocProvenanceTests(unittest.TestCase):
    def test_match_method_on_contradiction(self) -> None:
        uc = _minimal_uc()
        reqs = [
            ParsedRequirement(
                rule_id="a",
                source_kind=SourceKind.STRUCTURED_TEXT,
                ifc_entity="IfcWall",
                property_set="Pset_WallCommon",
                property_name="FireRating",
                expected_value="REI60",
            ),
            ParsedRequirement(
                rule_id="b",
                source_kind=SourceKind.CALCULATION,
                ifc_entity="IfcWall",
                property_set="Pset_WallCommon",
                property_name="FireRating",
                expected_value="REI90",
            ),
        ]
        issues = uc._detect_cross_document_contradictions(reqs)
        self.assertTrue(issues)
        self.assertEqual(issues[0].match_method, "entity+pset+prop")
        self.assertEqual(issues[0].origin, "deterministic")
        self.assertTrue(issues[0].evidence_refs)


class Phase7BcfXsdHonestyTests(unittest.TestCase):
    def test_xsd_dir_present_is_not_run_not_passed(self) -> None:
        from aerobim.domain.models import (
            FindingCategory,
            Severity,
            ValidationIssue,
            ValidationReport,
            ValidationSummary,
        )

        report = ValidationReport(
            report_id="r1",
            request_id="q1",
            ifc_path=Path("m.ifc"),
            created_at="2026-07-18T00:00:00+00:00",
            requirements=(),
            issues=(
                ValidationIssue(
                    rule_id="T1",
                    severity=Severity.ERROR,
                    message="x",
                    category=FindingCategory.IFC_VALIDATION,
                    element_guid="0123456789ABCDEFGHIJ_$",
                ),
            ),
            summary=ValidationSummary(
                requirement_count=0,
                issue_count=1,
                error_count=1,
                warning_count=0,
                passed=False,
            ),
        )
        archive = export_bcf(report)
        with tempfile.TemporaryDirectory() as tmp:
            xsd_dir = Path(tmp) / "xsd"
            xsd_dir.mkdir()
            (xsd_dir / "markup.xsd").write_text("<xs:schema/>", encoding="utf-8")
            result = verify_bcf_zip_structure(archive, xsd_dir=xsd_dir)
        self.assertEqual(result.xsd_status, "not_run")
        self.assertNotEqual(result.xsd_status, "passed")


if __name__ == "__main__":
    unittest.main()
