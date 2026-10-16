"""Pre-final IFC4x3 temp copy: free-space precheck and guaranteed cleanup."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from collections import namedtuple
from pathlib import Path
from unittest import mock

from aerobim.infrastructure.adapters import ifc_file_open as mod

REPO = Path(__file__).resolve().parents[2]
WALL = REPO / "samples" / "ifc" / "wall-pset-ifc4x3.ifc"
_Usage = namedtuple("_Usage", "total used free")


class TempCopyTests(unittest.TestCase):
    def setUp(self) -> None:
        self._work = tempfile.TemporaryDirectory()
        self.addCleanup(self._work.cleanup)
        self.work = Path(self._work.name)
        self.tmp = self.work / "tmp"
        self.tmp.mkdir()
        patcher = mock.patch.object(tempfile, "tempdir", str(self.tmp))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.src = self.work / "pre-final.ifc"
        self.src.write_text(
            WALL.read_text(encoding="utf-8").replace("'IFC4X3_ADD2'", "'IFC4X3_TC1'"),
            encoding="utf-8",
        )

    def _leftovers(self) -> list[Path]:
        return sorted(self.tmp.glob("aerobim-ifc4x3-*"))

    def test_copy_is_created_with_rewritten_header(self) -> None:
        copy = mod._pre_final_rewrite_copy(self.src)
        assert copy is not None
        try:
            self.assertIn("IFC4X3_ADD2", copy.read_text(encoding="utf-8")[:2000])
            self.assertEqual(copy.parent, self.tmp)
        finally:
            copy.unlink()

    def test_final_schema_needs_no_copy(self) -> None:
        self.assertIsNone(mod._pre_final_rewrite_copy(WALL))
        self.assertEqual(self._leftovers(), [])

    def test_low_disk_space_raises_clear_error_and_writes_nothing(self) -> None:
        with mock.patch.object(shutil, "disk_usage", return_value=_Usage(10, 10, 1024)):
            with self.assertRaises(mod.IfcTempSpaceError) as ctx:
                mod._pre_final_rewrite_copy(self.src)
        message = str(ctx.exception)
        self.assertIn("not enough free disk space", message)
        self.assertIn(str(self.tmp), message)
        self.assertIn("TMPDIR", message)
        self.assertEqual(self._leftovers(), [])

    def test_write_failure_removes_partial_copy(self) -> None:
        with mock.patch.object(shutil, "copyfileobj", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                mod._pre_final_rewrite_copy(self.src)
        self.assertEqual(self._leftovers(), [])

    def test_open_failure_on_copy_still_removes_it(self) -> None:
        class _SchemaError(Exception):
            pass

        fake = mock.Mock()
        fake.SchemaError = _SchemaError
        fake.open.side_effect = [_SchemaError("IFC4X3_TC1"), RuntimeError("parse failed")]
        with self.assertRaises(RuntimeError):
            mod._open_spf_compat(self.src, fake)
        self.assertEqual(fake.open.call_count, 2)
        self.assertEqual(self._leftovers(), [])

    def test_space_error_propagates_from_compat_open(self) -> None:
        class _SchemaError(Exception):
            pass

        fake = mock.Mock()
        fake.SchemaError = _SchemaError
        fake.open.side_effect = _SchemaError("IFC4X3_TC1")
        with mock.patch.object(shutil, "disk_usage", return_value=_Usage(10, 10, 0)):
            with self.assertRaises(mod.IfcTempSpaceError):
                mod._open_spf_compat(self.src, fake)
        self.assertEqual(self._leftovers(), [])


if __name__ == "__main__":
    unittest.main()
