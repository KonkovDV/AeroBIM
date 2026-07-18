"""Phase 2 provenance: stable finding_id, origin, BCF/JSON round-trip."""

from __future__ import annotations

import tempfile
import unittest
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from aerobim.domain.finding_provenance import (
    assert_finding_persistable,
    compute_stable_finding_id,
    ensure_finding_provenance,
    is_finding_publishable,
)
from aerobim.domain.models import (
    FindingCategory,
    ProblemZone,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.infrastructure.adapters.bcf_report_exporter import collect_bcf_topics, export_bcf
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore


class StableFindingIdTests(unittest.TestCase):
    def test_same_structure_same_id(self) -> None:
        left = ValidationIssue(
            rule_id="IDS-WALL-001",
            severity=Severity.ERROR,
            message="missing FireRating",
            category=FindingCategory.IFC_VALIDATION,
            element_guid="2O2Fr$t4X7Zf8NOew3FLOH",
            property_set="Pset_WallCommon",
            property_name="FireRating",
            source_id="ids-pack",
        )
        right = ValidationIssue(
            rule_id="IDS-WALL-001",
            severity=Severity.ERROR,
            message="different wording must not change id",
            category=FindingCategory.IFC_VALIDATION,
            element_guid="2O2Fr$t4X7Zf8NOew3FLOH",
            property_set="Pset_WallCommon",
            property_name="FireRating",
            source_id="ids-pack",
        )
        self.assertEqual(compute_stable_finding_id(left), compute_stable_finding_id(right))

    def test_ensure_is_deterministic_across_calls(self) -> None:
        issue = ValidationIssue(
            rule_id="AEROBIM-CLASH-CAPABILITY",
            severity=Severity.ERROR,
            message="clash failed",
            source_id="clash",
            element_guid="guid-a",
        )
        first = ensure_finding_provenance(issue)
        second = ensure_finding_provenance(issue)
        self.assertEqual(first.finding_id, second.finding_id)
        self.assertEqual(first.origin, "deterministic")
        self.assertTrue(is_finding_publishable(first))

    def test_weak_source_id_is_rewritten_and_publishable(self) -> None:
        stamped = ensure_finding_provenance(
            ValidationIssue(
                rule_id="R1",
                severity=Severity.WARNING,
                message="x",
                source_id="unspecified",
            )
        )
        self.assertNotEqual(stamped.source_id, "unspecified")
        assert_finding_persistable(stamped)

    def test_missing_evidence_not_publishable(self) -> None:
        issue = ValidationIssue(
            rule_id="R1",
            severity=Severity.ERROR,
            message="x",
            finding_id="abc",
            source_id="src",
            evidence_refs=(),
        )
        self.assertFalse(is_finding_publishable(issue))


class ProvenanceExportRoundTripTests(unittest.TestCase):
    def test_persist_reload_json_bcf_preserve_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = FilesystemAuditStore(root)
            ifc = root / "model.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            issue = ensure_finding_provenance(
                ValidationIssue(
                    rule_id="IDS-WALL-001",
                    severity=Severity.ERROR,
                    message="missing FireRating",
                    category=FindingCategory.IFC_VALIDATION,
                    element_guid="2O2Fr$t4X7Zf8NOew3FLOH",
                    property_set="Pset_WallCommon",
                    property_name="FireRating",
                    source_id="ids-pack",
                    evidence_refs=("ids-pack#ifc:2O2Fr$t4X7Zf8NOew3FLOH",),
                    problem_zone=ProblemZone(sheet_id="AR-01", page_number=1, x=0.1, y=0.2),
                    approval_ref="APPR-TEST-1",
                    tenant_id="tenant-a",
                    project_id="proj-1",
                    origin="deterministic",
                )
            )
            report = ValidationReport(
                report_id="f" * 32,
                request_id="p2-round-trip",
                ifc_path=ifc,
                created_at=datetime.now(tz=UTC).isoformat(),
                requirements=(),
                issues=(issue,),
                summary=ValidationSummary(0, 1, 1, 0, False),
                tenant_id="tenant-a",
                project_id="proj-1",
                schema_version="1.0.0",
            )
            store.save(report)
            loaded = store.get(report.report_id)
            assert loaded is not None
            reloaded = loaded.issues[0]
            self.assertEqual(reloaded.finding_id, issue.finding_id)
            self.assertEqual(reloaded.source_id, "ids-pack")
            self.assertEqual(reloaded.evidence_refs, issue.evidence_refs)
            self.assertEqual(reloaded.element_guid, "2O2Fr$t4X7Zf8NOew3FLOH")
            self.assertEqual(reloaded.origin, "deterministic")
            self.assertEqual(reloaded.approval_ref, "APPR-TEST-1")

            topics_a = collect_bcf_topics(loaded)
            topics_b = collect_bcf_topics(loaded)
            self.assertEqual(len(topics_a), 1)
            self.assertEqual(topics_a[0].topic_guid, topics_b[0].topic_guid)
            self.assertIn(f"finding_id={issue.finding_id}", topics_a[0].description)
            self.assertIn("2O2Fr$t4X7Zf8NOew3FLOH", topics_a[0].description)
            self.assertIn("ids-pack#ifc:2O2Fr$t4X7Zf8NOew3FLOH", topics_a[0].reference_links)

            blob = export_bcf(loaded)
            with zipfile.ZipFile(__import__("io").BytesIO(blob)) as zf:
                markup_name = next(name for name in zf.namelist() if name.endswith("markup.bcf"))
                markup = zf.read(markup_name).decode("utf-8")
            root_xml = ET.fromstring(markup)
            ns = {"m": "http://www.buildingsmart-tech.org/bcf/markup/2.1"}
            description = root_xml.find("m:Topic/m:Description", ns)
            assert description is not None and description.text is not None
            self.assertIn(f"finding_id={issue.finding_id}", description.text)
            self.assertIn("origin=deterministic", description.text)
            labels = [node.text for node in root_xml.findall("m:Topic/m:Labels", ns)]
            self.assertIn("origin:deterministic", labels)


if __name__ == "__main__":
    unittest.main()
