"""Pack probe: aggregate stays name-free; local rows stay in quarantine."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.tools.pack_probe import main, probe_pack


def _build_tree(root: Path) -> None:
    (root / "КЖ").mkdir(parents=True)
    (root / "КЖ" / "лист-вектор.pdf").write_bytes(b"%PDF-1.4 ... /Font ...")
    (root / "рабочая РД").mkdir()
    (root / "рабочая РД" / "скан.pdf").write_bytes(b"%PDF-1.4 no fonts here")
    (root / "модель.ifc").write_text(
        "ISO-10303-21;\nHEADER;\nFILE_SCHEMA(('IFC4'));\nENDSEC;",
        encoding="utf-8",
    )
    (root / "чертёж.dwg").write_bytes(b"AC1032 binary")
    (root / "регламент общих собраний.pdf").write_bytes(b"%PDF /Font x")
    (root / "расчётная модель.lir").write_bytes(b"\x00\x01")


class PackProbeTests(unittest.TestCase):
    def test_aggregate_counts_and_heuristics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pack"
            root.mkdir()
            _build_tree(root)
            rows, aggregate = probe_pack(root)

        self.assertEqual(aggregate["file_count"], 6)
        self.assertEqual(aggregate["by_ext"][".pdf"], 3)
        self.assertEqual(aggregate["by_section"]["КЖ"], 1)
        self.assertEqual(aggregate["by_tz_class"]["2"], 1)
        self.assertEqual(aggregate["by_tz_class"]["6"], 1)
        self.assertEqual(aggregate["notes"]["pdf_vector"], 2)
        self.assertEqual(aggregate["notes"]["pdf_scan"], 1)
        self.assertEqual(aggregate["notes"]["ifc_IFC4"], 1)
        self.assertEqual(aggregate["notes"]["ord_candidate"], 1)
        self.assertEqual(aggregate["notes"]["dwg_magic_AC1032"], 1)
        self.assertEqual(len(rows), 6)
        self.assertTrue(all("path" in row for row in rows))

    def test_aggregate_never_contains_names_paths_or_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pack"
            root.mkdir()
            _build_tree(root)
            _, aggregate = probe_pack(root)
            blob = json.dumps(aggregate, ensure_ascii=False)

        self.assertFalse(aggregate["names_in_output"])
        self.assertFalse(aggregate["hashes_in_output"])
        for forbidden in ("лист-вектор", "скан.pdf", "модель.ifc", "чертёж"):
            self.assertNotIn(forbidden, blob)
        self.assertNotIn("sha256", blob)
        self.assertNotIn('"path"', blob)

    def test_main_writes_two_outputs_outside_git(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pack"
            out = Path(tmp) / "out"
            root.mkdir()
            _build_tree(root)
            self.assertEqual(main([str(root), str(out)]), 0)
            local = json.loads((out / "pack-local.json").read_text(encoding="utf-8"))
            aggregate = json.loads((out / "pack-aggregate.json").read_text(encoding="utf-8"))
        self.assertEqual(len(local), 6)
        self.assertIn("sha256", json.dumps(local))
        self.assertEqual(aggregate["file_count"], 6)
        self.assertFalse(aggregate["names_in_output"])


if __name__ == "__main__":
    unittest.main()
