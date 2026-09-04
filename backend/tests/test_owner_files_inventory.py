
"""Owner-files inventory never writes into the git-tracked tree."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.owner_files_inventory import (
    PUBLIC_REHEARSAL,
    output_is_local_only,
    public_rehearsal_snapshot,
    require_local_only_output,
    scan_owner_files,
)
from aerobim.tools.inventory_owner_files import main as inventory_main

_REPO = Path(__file__).resolve().parents[2]


class OwnerFilesInventoryTests(unittest.TestCase):
    def test_public_rehearsal_has_no_names_or_hashes(self) -> None:
        snap = public_rehearsal_snapshot()
        self.assertEqual(snap["checkpoint"], CHECKPOINT)
        self.assertFalse(snap["names_in_git"])
        self.assertFalse(snap["hashes_in_git"])
        self.assertFalse(snap["raise_cap"])
        self.assertEqual(snap["ifc_count"], PUBLIC_REHEARSAL["ifc_count"])
        self.assertEqual(snap["native_navis_count"], 21)
        self.assertEqual(snap["remark_named_count"], 70)
        self.assertEqual(snap["typical_remarks_checklist_count"], 2)
        self.assertNotIn("pack_hash", snap)
        self.assertNotIn("pack_folder_labels", snap)
        self.assertNotIn("sha256", snap)

    def test_git_tracked_output_is_rejected(self) -> None:
        self.assertFalse(output_is_local_only(_REPO, _REPO / "docs" / "evidence" / "leak.json"))
        self.assertTrue(output_is_local_only(_REPO, _REPO / ".local" / "files-pack-inventory.json"))
        with self.assertRaises(ValueError):
            require_local_only_output(_REPO, _REPO / "docs" / "evidence" / "leak.json")

    def test_scan_tmp_tree_counts_suffixes(self) -> None:
        with self._tmp_tree() as root:
            scan = scan_owner_files(root, include_names=False)
        self.assertEqual(scan["status"], "SCANNED_LOCAL")
        self.assertEqual(scan["ifc_count"], 2)
        self.assertEqual(scan["ifc_over_default_cap_count"], 0)
        self.assertFalse(scan["names_in_payload"])
        self.assertNotIn("pack_folder_labels", scan)

    def test_scan_counts_remark_names_without_leaking_them(self) -> None:
        with self._tmp_tree() as root:
            scan = scan_owner_files(root, include_names=False)
        self.assertEqual(scan["remark_named_count"], 2)
        self.assertEqual(scan["typical_remarks_checklist_count"], 1)
        self.assertFalse(scan["names_in_payload"])
        serialized = json.dumps(scan, ensure_ascii=False)
        self.assertNotIn("Замечания", serialized)

    def test_rehearsal_differs_flags_remark_drift(self) -> None:
        from aerobim.domain.owner_files_inventory import rehearsal_differs

        scan = {
            "status": "SCANNED_LOCAL",
            **{key: PUBLIC_REHEARSAL[key] for key in PUBLIC_REHEARSAL if key != "rehearsal_date"},
        }
        self.assertFalse(rehearsal_differs(scan))
        scan["typical_remarks_checklist_count"] = 0
        self.assertTrue(rehearsal_differs(scan))

    def test_cli_refuses_docs_output(self) -> None:
        target = _REPO / "docs" / "evidence" / "must-not-write-inventory.json"
        code = inventory_main(["--root", str(_REPO / "samples"), "--output", str(target)])
        self.assertEqual(code, 2)
        self.assertFalse(target.exists())

    def test_cli_writes_tmp_outside_repo(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "inv.json"
            with self._tmp_tree() as tree:
                code = inventory_main(["--root", str(tree), "--output", str(out)])
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["ifc_count"], 2)
            self.assertTrue(payload["names_must_not_enter_git"])

    def _tmp_tree(self):
        import tempfile
        from contextlib import contextmanager

        @contextmanager
        def _ctx():
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "files"
                house = root / "house_a"
                house.mkdir(parents=True)
                (house / "a.ifc").write_bytes(b"ISO-10303-21;" + b" " * 32)
                (house / "b.ifc").write_bytes(b"ISO-10303-21;" + b" " * 32)
                (house / "sheet.pdf").write_bytes(b"%PDF")
                (house / "Замечания к разделу АР.pdf").write_bytes(b"%PDF")
                (house / "Типовые замечания при приёмке.xlsx").write_bytes(b"PK")
                yield root

        return _ctx()


if __name__ == "__main__":
    unittest.main()
