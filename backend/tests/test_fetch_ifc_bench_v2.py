"""IFC-Bench fetch skips GPLv3 project paths."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.tools.fetch_ifc_bench_v2 import _is_gpl_path, copy_local


class FetchIfcBenchV2Tests(unittest.TestCase):
    def test_source_has_no_machine_absolute_plans_path(self) -> None:
        src = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "aerobim"
            / "tools"
            / "fetch_ifc_bench_v2.py"
        )
        text = src.read_text(encoding="utf-8")
        self.assertNotIn(r"C:\plans", text)
        self.assertNotIn("C:/plans", text)
    def test_gpl_paths_detected(self) -> None:
        excludes = {"4351", "hitos"}
        self.assertTrue(_is_gpl_path("projects/4351/arc.ifc", excludes))
        self.assertFalse(_is_gpl_path("projects/duplex/mep.ifc", excludes))

    def test_copy_skips_gpl_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            (src / "projects" / "duplex").mkdir(parents=True)
            (src / "projects" / "hitos").mkdir(parents=True)
            (src / "projects" / "duplex" / "arc.ifc").write_text("ok", encoding="utf-8")
            (src / "projects" / "hitos" / "arc.ifc").write_text("gpl", encoding="utf-8")
            copied = copy_local(src, dest, excludes={"hitos"})
        paths = {item["path"] for item in copied}
        self.assertIn("projects/duplex/arc.ifc", paths)
        self.assertNotIn("projects/hitos/arc.ifc", paths)


if __name__ == "__main__":
    unittest.main()
