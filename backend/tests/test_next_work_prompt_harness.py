"""Harness polish for RT-001/002/003 next-work prompt (no NO_GO flip)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.infrastructure.adapters.ifc_file_open import (
    configure_ifc_parse_cache,
    reset_ifc_parse_cache_for_tests,
)
from aerobim.tools.export_detections_from_report import (
    build_detections_document,
    findings_from_report_payload,
)

REPO = Path(__file__).resolve().parents[2]


class ExportDetectionsFromReportTests(unittest.TestCase):
    def test_maps_issues_to_detections_shape(self) -> None:
        report = {
            "issues": [
                {
                    "rule_id": "SPATIAL-HARD-CLASH",
                    "category": "spatial",
                    "target_ref": "A|B",
                    "finding_id": "f1",
                },
                {
                    "rule_id": "CROSS-DOC-1",
                    "category": "cross_document",
                    "element_guid": "guid-1",
                },
            ]
        }
        findings = findings_from_report_payload(report, case_id="CUST-AR-001", discipline="ar")
        self.assertEqual(len(findings), 2)
        self.assertEqual(findings[0]["finding_class"], "clash")
        doc = build_detections_document(
            run_id="run-1",
            case_id="CUST-AR-001",
            report_payload=report,
            discipline="ar",
        )
        self.assertEqual(doc["schema_version"], "1.0.0")
        self.assertEqual(doc["cases"][0]["discipline"], "ar")


class LabelsSchemaCustomerTemplateTests(unittest.TestCase):
    def test_customer_protocol_template_validates(self) -> None:
        import jsonschema

        schema = json.loads(
            (
                REPO / "samples" / "benchmarks" / "detection-precision" / "labels.schema.json"
            ).read_text(encoding="utf-8")
        )
        template = json.loads(
            (
                REPO
                / "samples"
                / "benchmarks"
                / "detection-precision"
                / "labels-customer-protocol-template.json"
            ).read_text(encoding="utf-8")
        )
        errors = list(jsonschema.Draft202012Validator(schema).iter_errors(template))
        self.assertEqual(errors, [], [e.message for e in errors])


class IfcParseCacheTests(unittest.TestCase):
    def tearDown(self) -> None:
        reset_ifc_parse_cache_for_tests()

    def test_configure_creates_cache_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_ifc_parse_cache(tmp)
            self.assertTrue(Path(tmp).is_dir())
            reset_ifc_parse_cache_for_tests()


class MepMatrixTemplateExistsTests(unittest.TestCase):
    def test_clearance_matrix_template_present(self) -> None:
        path = REPO / "samples" / "mep" / "clearance-matrix-template.json"
        self.assertTrue(path.is_file())
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("claim_boundary", payload)
        self.assertIn("RT-003", payload["claim_boundary"])


if __name__ == "__main__":
    unittest.main()
