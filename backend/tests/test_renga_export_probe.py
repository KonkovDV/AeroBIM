"""Renga IFC probe: originating system + MOEXP IFC4 fail-closed. Not Samolet."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.domain.ids_schema_gate import parse_ifc_file_name
from aerobim.tools.run_renga_export_probe import (
    build_payload,
    classify_originating_system,
    main,
    probe_ifc,
    resolve_ifc_path,
    skipped_payload,
)

REPO = Path(__file__).resolve().parents[2]
WALLS = REPO / "samples" / "ifc" / "walls-multi-entity.ifc"
IFC4X3 = REPO / "samples" / "ifc" / "wall-pset-ifc4x3.ifc"
MOEXP_AR = (
    REPO
    / "samples"
    / "ids"
    / "moexp"
    / "pack"
    / "oks"
    / "IDS_v1.0_Требования_МОГЭ_к_ЦИМ_АР_v3.2.ids"
)

_RENGA_SHAPE_IFC = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition[DesignTransferView]'),'2;1');
FILE_NAME('renga-shape.ifc','2024-01-01T00:00:00',('Renga'),('Org'),'Renga 8.7','Renga','');
FILE_SCHEMA(('IFC4X3'));
ENDSEC;
DATA;
#1=IFCPROJECT('3JnsKeWMP9xBNxnCYr$wB9',$,'Header-shape fixture not a Renga binary',$,$,$,$,$,$);
#2=IFCAPPLICATION(#1,'8.7','Renga','Renga');
ENDSEC;
END-ISO-10303-21;
"""


class RengaExportProbeTests(unittest.TestCase):
    def test_demo_ifc_file_name_is_ifcopenshell_not_renga(self) -> None:
        header = WALLS.read_text(encoding="utf-8")
        parsed = parse_ifc_file_name(header)
        assert parsed is not None
        self.assertIn("IfcOpenShell", parsed.originating_system)
        self.assertEqual(
            classify_originating_system(
                preprocessor_version=parsed.preprocessor_version,
                originating_system=parsed.originating_system,
                applications=(),
            ),
            "ifcopenshell",
        )

    def test_parse_file_name_with_author_list(self) -> None:
        header = (
            "FILE_NAME('a.ifc','2024-01-01T00:00:00',"
            "('Ann','Bob'),('Org'),'Renga 8.7','Renga','');\n"
        )
        parsed = parse_ifc_file_name(header)
        assert parsed is not None
        self.assertEqual(parsed.originating_system, "Renga")
        self.assertEqual(parsed.preprocessor_version, "Renga 8.7")

    def test_parse_renga_87_ifcplusplus_file_name(self) -> None:
        header = (
            "FILE_NAME('24-1-17_22_K1_C1_MF_1_Rn87_I4021.ifc','2025-07-29T09:49:34',"
            "('zatom'),(''),'IfcPlusPlus','Renga Professional 8.7.20879.0','');\n"
        )
        parsed = parse_ifc_file_name(header)
        assert parsed is not None
        self.assertEqual(parsed.originating_system, "Renga Professional 8.7.20879.0")
        self.assertEqual(parsed.preprocessor_version, "IfcPlusPlus")
        self.assertEqual(
            classify_originating_system(
                preprocessor_version=parsed.preprocessor_version,
                originating_system=parsed.originating_system,
                applications=(),
            ),
            "renga",
        )

    def test_skipped_payload_does_not_close_samolet_intake(self) -> None:
        payload = skipped_payload(reason="missing")
        self.assertEqual(payload["status"], "SKIPPED")
        self.assertFalse(payload["samolet_export"])
        self.assertFalse(payload["closes_c4_samolet_intake"])
        self.assertFalse(payload["vertical_slice_ifc_replaced"])
        self.assertEqual(payload["checkpoint"], "NO_GO")

    def test_resolve_missing_pack_is_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = resolve_ifc_path(None, repo=Path(tmp), env={})
        self.assertIsNone(missing)

    def test_ifc4x3_fixture_fail_closes_moexp_and_is_not_renga(self) -> None:
        row = probe_ifc(IFC4X3, MOEXP_AR, repo=REPO)
        self.assertEqual(row["model_schema"], "IFC4X3")
        self.assertGreater(row["schema_mismatch_count"], 0)
        self.assertTrue(row["schema_fail_closed"])
        self.assertFalse(row["is_renga_export"])
        self.assertEqual(row["originating_family"], "ifcopenshell")
        self.assertFalse(row["samolet_export"])
        self.assertFalse(row["publisher_pnst909_sample"])

    def test_renga_shaped_header_is_classified_and_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "renga-shape.ifc"
            path.write_text(_RENGA_SHAPE_IFC, encoding="utf-8")
            row = probe_ifc(path, MOEXP_AR, repo=REPO)
        self.assertTrue(row["is_renga_export"])
        self.assertEqual(row["originating_family"], "renga")
        self.assertEqual(row["model_schema"], "IFC4X3")
        self.assertTrue(row["schema_fail_closed"])
        self.assertFalse(row["publisher_pnst909_sample"])
        self.assertFalse(row["samolet_export"])

    def test_demo_ifc_vs_moexp_is_schema_ok_and_not_renga(self) -> None:
        row = probe_ifc(WALLS, MOEXP_AR, repo=REPO)
        self.assertEqual(row["model_schema"], "IFC4")
        self.assertFalse(row["is_renga_export"])
        self.assertEqual(row["schema_mismatch_count"], 0)
        self.assertFalse(row["schema_fail_closed"])

    def test_build_payload_skipped_when_missing(self) -> None:
        payload = build_payload(
            ifc_path=REPO / ".local" / "renga-pnst909" / "missing.ifc",
            ids_path=MOEXP_AR,
            repo=REPO,
        )
        self.assertEqual(payload["status"], "SKIPPED")
        self.assertIn("content_sha256", payload)

    def test_require_renga_exits_2_on_ifcopenshell_fixture(self) -> None:
        code = main(["--ifc", str(WALLS), "--ids", str(MOEXP_AR), "--require-renga"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
