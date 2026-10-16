"""Pre-final IFC4x3 headers open as IFC4X3_ADD2; genuine parse failures still raise."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.domain.ifc4x3_schema_compat import is_pre_final_ifc4x3, rewrite_header_schema

_FIXTURE = Path(__file__).resolve().parents[2] / "samples" / "ifc" / "wall-pset-ifc4x3.ifc"


def _variant(tmp: str, token: str, *, break_data: bool = False) -> Path:
    data = _FIXTURE.read_bytes().replace(
        b"FILE_SCHEMA(('IFC4X3_ADD2'));", f"FILE_SCHEMA(('{token}'));".encode()
    )
    if break_data:
        data = data.replace(b"#6=IFCWALL(", b"#6=IFCNOTANENTITY(")
    path = Path(tmp) / f"{token}.ifc"
    path.write_bytes(data)
    return path


class RewriteHeaderTests(unittest.TestCase):
    def test_rewrites_only_pre_final_tokens(self) -> None:
        for token in ("IFC4X3", "IFC4X3_ADD1", "IFC4X3_TC1"):
            out, original = rewrite_header_schema(f"FILE_SCHEMA(('{token}'));".encode())
            self.assertEqual(out, b"FILE_SCHEMA(('IFC4X3_ADD2'));")
            self.assertEqual(original, token)
        for token in ("IFC4X3_ADD2", "IFC4", "IFC2X3"):
            out, original = rewrite_header_schema(f"FILE_SCHEMA(('{token}'));".encode())
            self.assertIsNone(original)
        self.assertTrue(is_pre_final_ifc4x3("ifc4x3_tc1"))
        self.assertFalse(is_pre_final_ifc4x3(None))


class OpenPreFinalTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            import ifcopenshell  # noqa: F401
        except ImportError:
            self.skipTest("ifcopenshell not installed")
        from aerobim.infrastructure.adapters import ifc_file_open

        self.mod = ifc_file_open
        ifc_file_open.reset_ifc_parse_cache_for_tests()
        self.addCleanup(ifc_file_open.reset_ifc_parse_cache_for_tests)

    def test_each_ifc4x3_variant_opens(self) -> None:
        for token in ("IFC4X3", "IFC4X3_ADD1", "IFC4X3_TC1", "IFC4X3_ADD2"):
            with self.subTest(token=token), tempfile.TemporaryDirectory() as tmp:
                path = _variant(tmp, token)
                model = self.mod.open_ifc_model(path)
                self.assertTrue(str(model.schema).upper().startswith("IFC4X3"))
                self.assertEqual(len(model.by_type("IfcWall")), 1)
                leftovers = list(Path(tempfile.gettempdir()).glob("aerobim-ifc4x3-*.ifc"))
                self.assertEqual(leftovers, [])

    def test_unparseable_pre_final_file_is_rejected(self) -> None:
        import ifcopenshell

        if not str(ifcopenshell.version).startswith("0.9"):
            self.skipTest("fallback path exists only on kernels without pre-final schemas")
        with tempfile.TemporaryDirectory() as tmp:
            path = _variant(tmp, "IFC4X3_TC1", break_data=True)
            with self.assertRaises(self.mod.IfcPreFinalSchemaError):
                self.mod.open_ifc_model(path)
