"""Official IDS 1.0 XSD audit (Wave F, Jul 2026).

Anchors: buildingSMART IDS 1.0.0 schema (github.com/buildingSMART/IDS, master);
IDS-Audit-tool practice — schema audit before semantic audit. Claim boundary:
schema-valid IDS ≠ requirement correctness; fail-honest WARNING when the
validator/schema is unavailable, never silent OK.
"""

from __future__ import annotations

import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aerobim.domain.models import Severity
from aerobim.infrastructure.adapters.xml_ids_document_auditor import (
    XmlIdsDocumentAuditor,
    default_ids_xsd_path,
)

_SAMPLES = Path(__file__).resolve().parents[2] / "samples"

_VALID_IDS = """<?xml version="1.0" encoding="UTF-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://standards.buildingsmart.org/IDS ids.xsd">
  <info><title>Wave F fixture</title></info>
  <specifications>
    <specification name="Walls" ifcVersion="IFC4">
      <applicability minOccurs="0" maxOccurs="unbounded">
        <entity><name><simpleValue>IFCWALL</simpleValue></name></entity>
      </applicability>
      <requirements>
        <attribute cardinality="required">
          <name><simpleValue>Name</simpleValue></name>
        </attribute>
      </requirements>
    </specification>
  </specifications>
</ids>
"""


class IdsOfficialXsdAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            import xmlschema  # noqa: F401
        except ImportError:
            self.skipTest("xmlschema not installed")

    def test_vendored_schema_is_discovered(self) -> None:
        path = default_ids_xsd_path()
        self.assertIsNotNone(path)
        assert path is not None
        self.assertTrue(path.is_file())

    def test_repo_ids_fixtures_pass_official_xsd(self) -> None:
        auditor = XmlIdsDocumentAuditor()
        for fixture in sorted((_SAMPLES / "ids").glob("*.ids")):
            issues = auditor.audit(fixture)
            self.assertEqual(
                [i for i in issues if i.rule_id == "AEROBIM-IDS-XSD-INVALID"],
                [],
                msg=f"{fixture.name}: {[i.message for i in issues]}",
            )

    def test_schema_invalid_ids_yields_error(self) -> None:
        # Missing required ifcVersion attribute + bogus element.
        broken = _VALID_IDS.replace(' ifcVersion="IFC4"', "").replace(
            "<requirements>", "<requirements><bogusFacet/>"
        )
        with tempfile.TemporaryDirectory() as tmp:
            ids_path = Path(tmp) / "broken.ids"
            ids_path.write_text(broken, encoding="utf-8")
            issues = XmlIdsDocumentAuditor().audit(ids_path)
        xsd_errors = [i for i in issues if i.rule_id == "AEROBIM-IDS-XSD-INVALID"]
        self.assertTrue(xsd_errors)
        self.assertTrue(all(i.severity == Severity.ERROR for i in xsd_errors))
        self.assertTrue(all(i.origin == "deterministic" for i in xsd_errors))

    def test_missing_schema_is_explicit_warning_never_silent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ids_path = Path(tmp) / "doc.ids"
            ids_path.write_text(_VALID_IDS, encoding="utf-8")
            auditor = XmlIdsDocumentAuditor(xsd_path=Path(tmp) / "absent.xsd")
            issues = auditor.audit(ids_path)
        capability = [i for i in issues if i.rule_id == "AEROBIM-IDS-XSD-CAPABILITY"]
        self.assertEqual(len(capability), 1)
        self.assertEqual(capability[0].severity, Severity.WARNING)

    def test_valid_document_produces_no_xsd_issues(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ids_path = Path(tmp) / "valid.ids"
            ids_path.write_text(_VALID_IDS, encoding="utf-8")
            issues = XmlIdsDocumentAuditor().audit(ids_path)
        self.assertEqual(
            [i for i in issues if i.rule_id.startswith("AEROBIM-IDS-XSD")],
            [],
            msg=[i.message for i in issues],
        )

    def test_validation_is_offline_no_outbound_fetch(self) -> None:
        """SSRF guard: W3C imports resolve to xmlschema bundled copies."""

        def _blocked(*args: object, **kwargs: object) -> None:
            raise AssertionError("outbound network call from IDS XSD validation")

        with tempfile.TemporaryDirectory() as tmp:
            ids_path = Path(tmp) / "valid.ids"
            ids_path.write_text(_VALID_IDS, encoding="utf-8")
            with (
                patch.object(socket, "getaddrinfo", _blocked),
                patch.object(socket, "create_connection", _blocked),
            ):
                issues = XmlIdsDocumentAuditor().audit(ids_path)
        self.assertEqual(
            [i for i in issues if i.rule_id.startswith("AEROBIM-IDS-XSD")],
            [],
            msg=[i.message for i in issues],
        )


if __name__ == "__main__":
    unittest.main()
