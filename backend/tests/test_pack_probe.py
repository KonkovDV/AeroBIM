
"""Pack probe: aggregate stays name-free; local rows stay in quarantine."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT
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
    (root / "objA" / "КЖ").mkdir(parents=True)
    (root / "objA" / "АР").mkdir()
    (root / "objA" / "КЖ" / "kzh.pdf").write_bytes(b"%PDF-1.4 /Font complete")
    (root / "objA" / "АР" / "model.ifc").write_text(
        "ISO-10303-21;\nHEADER;\nFILE_SCHEMA(('IFC4'));\nENDSEC;",
        encoding="utf-8",
    )


class PackProbeTests(unittest.TestCase):
    def test_aggregate_counts_and_heuristics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pack"
            root.mkdir()
            _build_tree(root)
            rows, aggregate = probe_pack(root)

        self.assertEqual(aggregate["file_count"], 8)
        self.assertEqual(aggregate["checkpoint"], CHECKPOINT)
        self.assertEqual(aggregate["by_ext"][".pdf"], 4)
        self.assertEqual(aggregate["by_section"]["КЖ"], 2)
        self.assertEqual(aggregate["by_tz_class"]["2"], 1)
        self.assertEqual(aggregate["by_tz_class"]["6"], 1)
        self.assertEqual(aggregate["notes"]["pdf_vector"], 3)
        self.assertEqual(aggregate["notes"]["pdf_scan"], 1)
        self.assertEqual(aggregate["notes"]["ifc_IFC4"], 2)
        self.assertEqual(aggregate["notes"]["ord_candidate"], 1)
        self.assertEqual(aggregate["notes"]["dwg_magic_AC1032"], 1)
        self.assertEqual(len(rows), 8)
        self.assertTrue(all("path" in row for row in rows))
        self.assertFalse(aggregate["raises_spf_default"])
        self.assertEqual(aggregate["spf_cap_bytes"], 256 * 1024 * 1024)
        self.assertIn("yes", {row["processed_now"] for row in rows})
        self.assertIn("no", {row["processed_now"] for row in rows})
        self.assertTrue(any(row["legal_flag"] == "internal_regs_skip" for row in rows))
        self.assertEqual(aggregate["objects_runnable_complete"], 1)
        self.assertEqual(aggregate["lira_named_ext_files"], 1)
        self.assertFalse(aggregate["uncompressed_gib_in_git"])
        self.assertEqual(aggregate["tz_class_2_rd_files"], 1)
        self.assertEqual(aggregate["priority_counts"]["1"], 2)
        self.assertGreater(aggregate["unsupported_now_pct"], 0)
        self.assertEqual(aggregate["files_by_bucket"]["ifc"], 2)
        self.assertTrue(aggregate["archives_unexpanded"])
        p1 = [row for row in rows if row["priority"] == 1]
        self.assertEqual({row["ext"] for row in p1}, {".ifc", ".pdf"})
        self.assertTrue(all(row["object_key"] == "objA" for row in p1))

    def test_aggregate_never_contains_names_paths_or_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pack"
            root.mkdir()
            _build_tree(root)
            _, aggregate = probe_pack(root)
            blob = json.dumps(aggregate, ensure_ascii=False)

        self.assertFalse(aggregate["names_in_output"])
        self.assertFalse(aggregate["hashes_in_output"])
        for forbidden in ("лист-вектор", "скан.pdf", "модель.ifc", "чертёж", "objA"):
            self.assertNotIn(forbidden, blob)
        self.assertNotIn("sha256", blob)
        self.assertNotIn('"path"', blob)

    def test_wrapper_dir_is_not_the_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pack"
            wrap = root / "wrap"
            site = wrap / "site-one"
            (site / "ОВ").mkdir(parents=True)
            (site / "ВК").mkdir()
            (site / "ОВ" / "a.ifc").write_text(
                "ISO-10303-21;\nHEADER;\nFILE_SCHEMA(('IFC2X3'));\nENDSEC;",
                encoding="utf-8",
            )
            (site / "ВК" / "b.pdf").write_bytes(b"%PDF /Font")
            _, aggregate = probe_pack(root)
        self.assertEqual(aggregate["object_count"], 1)
        self.assertEqual(aggregate["objects_runnable_complete"], 1)
        self.assertNotIn("site-one", json.dumps(aggregate))
        self.assertNotIn("wrap", json.dumps(aggregate))

    def test_main_writes_two_outputs_outside_git(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pack"
            out = Path(tmp) / "out"
            root.mkdir()
            _build_tree(root)
            self.assertEqual(main([str(root), str(out)]), 0)
            local = json.loads((out / "pack-local.json").read_text(encoding="utf-8"))
            aggregate = json.loads((out / "pack-aggregate.json").read_text(encoding="utf-8"))
            tsv = (out / "pack-tracker.tsv").read_text(encoding="utf-8-sig")
            self.assertTrue((out / "pack-chat-summary.md").is_file())
        self.assertEqual(len(local), 8)
        self.assertIn("sha256", json.dumps(local))
        self.assertEqual(aggregate["file_count"], 8)
        self.assertFalse(aggregate["names_in_output"])
        self.assertIn("processed_now", tsv)

    def test_main_refuses_output_inside_docs(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pack"
            root.mkdir()
            _build_tree(root)
            self.assertEqual(main([str(root), str(repo / "docs" / "evidence")]), 2)


if __name__ == "__main__":
    unittest.main()
