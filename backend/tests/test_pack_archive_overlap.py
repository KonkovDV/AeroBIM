"""Archive overlap: zip members vs extracted siblings; aggregate stays nameless."""

from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from aerobim.tools.pack_archive_overlap import (
    extract_all_zips,
    extract_missing_ifc_pdf,
    extract_one_zip,
    main,
    probe_archives,
)


def _zip_with(path: Path, members: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, payload in members.items():
            info = zipfile.ZipInfo(name)
            archive.writestr(info, payload)


class PackArchiveOverlapTests(unittest.TestCase):
    def test_fully_on_disk_when_sibling_matches_size(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pack"
            unpacked = root / "_unpacked" / "site"
            unpacked.mkdir(parents=True)
            payload = b"%PDF-1.4 overlap"
            (unpacked / "a.pdf").write_bytes(payload)
            _zip_with(root / "site.zip", {"site/a.pdf": payload})
            rows, aggregate = probe_archives(root)
        self.assertEqual(aggregate["notes"]["fully_on_disk"], 1)
        self.assertEqual(rows[0]["missing_count"], 0)
        self.assertFalse(aggregate["recommend_extract_ifc_pdf"])
        self.assertNotIn("site", json.dumps(aggregate))

    def test_missing_ifc_is_counted_and_extractable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pack"
            dest = Path(tmp) / "out"
            root.mkdir()
            ifc = b"ISO-10303-21;\nHEADER;\nENDSEC;"
            _zip_with(root / "only.zip", {"x.ifc": ifc, "skip.dwg": b"AC1032"})
            rows, aggregate = probe_archives(root)
            self.assertEqual(rows[0]["status"], "not_on_disk")
            self.assertEqual(rows[0]["missing_ifc_pdf_count"], 1)
            self.assertTrue(aggregate["recommend_extract_ifc_pdf"])
            result = extract_missing_ifc_pdf(root, dest)
            self.assertEqual(result["written"], 1)
            ifc_files = list(dest.glob("*.ifc"))
            self.assertEqual(len(ifc_files), 1)
            self.assertEqual(ifc_files[0].read_bytes(), ifc)

    def test_extract_all_writes_non_ifc_members_and_blocks_slip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pack"
            dest = Path(tmp) / "out"
            root.mkdir()
            _zip_with(
                root / "site.zip",
                {
                    "ok.dwg": b"AC1032xxxx",
                    "../escape.txt": b"nope",
                },
            )
            result = extract_all_zips(root, dest)
            self.assertEqual(result["ok"], 1)
            self.assertEqual(result["slip"], 1)
            dwg = list(dest.rglob("ok.dwg"))
            self.assertEqual(len(dwg), 1)
            self.assertEqual(dwg[0].read_bytes(), b"AC1032xxxx")
            self.assertFalse((dest.parent / "escape.txt").exists())

    def test_extract_one_skips_existing_same_size(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "a.zip"
            dest = root / "out"
            _zip_with(archive, {"x.bin": b"hello"})
            dest.mkdir()
            first = extract_one_zip(archive, dest)
            second = extract_one_zip(archive, dest)
            self.assertEqual(first["ok"], 1)
            self.assertEqual(second["skip_exists"], 1)

    def test_main_refuses_docs(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pack"
            root.mkdir()
            _zip_with(root / "a.zip", {"a.pdf": b"%PDF"})
            self.assertEqual(main([str(root), str(repo / "docs" / "evidence")]), 2)


if __name__ == "__main__":
    unittest.main()
