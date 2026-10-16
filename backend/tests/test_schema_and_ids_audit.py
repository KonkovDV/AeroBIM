"""Tests for IFC schema pre-gate and IDS document audit."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.infrastructure.adapters.basic_ifc_schema_validator import BasicIfcSchemaValidator
from aerobim.infrastructure.adapters.xml_ids_document_auditor import XmlIdsDocumentAuditor


class BasicIfcSchemaValidatorTests(unittest.TestCase):
    def test_accepts_sample_ifc(self) -> None:
        samples = Path(__file__).resolve().parents[2] / "samples" / "ifc"
        ifc_files = list(samples.glob("*.ifc")) if samples.exists() else []
        if not ifc_files:
            raise unittest.SkipTest("no IFC fixtures")
        issues = BasicIfcSchemaValidator().validate_schema(ifc_files[0])
        self.assertEqual(issues, [])

    def test_rejects_non_spf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.ifc"
            path.write_text("not an ifc file", encoding="utf-8")
            issues = BasicIfcSchemaValidator().validate_schema(path)
        self.assertTrue(any(i.rule_id == "AEROBIM-IFC-SCHEMA" for i in issues))

    def _schema_issues(self, token: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "m.ifc"
            path.write_text(
                "ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION((''),'2;1');\n"
                "FILE_NAME('m','2026-01-01T00:00:00',(''),(''),'','','');\n"
                f"FILE_SCHEMA(('{token}'));\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;\n",
                encoding="utf-8",
            )
            return [i.message for i in BasicIfcSchemaValidator().validate_schema(path)]

    def test_ifc4x3_add2_supported(self) -> None:
        self.assertEqual(self._schema_issues("IFC4X3_ADD2"), [])

    def test_pre_final_ifc4x3_rejected_with_reexport_hint(self) -> None:
        # IfcOpenShell 0.9 cannot open these; the pre-gate must not call them supported.
        for token in ("IFC4X3", "IFC4X3_ADD1", "IFC4X3_TC1"):
            with self.subTest(token=token):
                messages = self._schema_issues(token)
                self.assertTrue(any("re-export as IFC4X3_ADD2" in m for m in messages))


class XmlIdsDocumentAuditorTests(unittest.TestCase):
    def test_accepts_sample_ids(self) -> None:
        samples = Path(__file__).resolve().parents[2] / "samples" / "ids"
        ids_files = list(samples.glob("*.ids")) if samples.exists() else []
        if not ids_files:
            raise unittest.SkipTest("no IDS fixtures")
        issues = XmlIdsDocumentAuditor().audit(ids_files[0])
        self.assertEqual(issues, [])

    def test_rejects_malformed_xml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.ids"
            path.write_text("<ids><broken>", encoding="utf-8")
            issues = XmlIdsDocumentAuditor().audit(path)
        self.assertTrue(any(i.rule_id == "AEROBIM-IDS-AUDIT" for i in issues))


if __name__ == "__main__":
    unittest.main()
