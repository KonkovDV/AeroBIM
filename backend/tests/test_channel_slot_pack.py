"""Channel slot assemble: existing files only, no fixture IDS."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.domain.channel_slot_pack import (
    UNSIGNED_IDS_REL,
    assert_ids_allowed,
    pick_drawings,
    pick_primary_ifc,
)
from aerobim.tools.benchmark_project_package import repo_root


class ChannelSlotPackTests(unittest.TestCase):
    def test_prefers_kr_when_ar_is_over_spf_cap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ar = root / "HOUSE_00_АР_ПД.ifc"
            kr = root / "HOUSE_00_КР_ПД.ifc"
            ar.write_bytes(b"IFC" + b"0" * 50)
            kr.write_bytes(b"IFC" + b"0" * 20)
            chosen = pick_primary_ifc([ar, kr], cap_bytes=40)
            self.assertEqual(chosen, kr)

    def test_prefers_largest_under_cap_ar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            small = root / "A_АР_ПД.ifc"
            large = root / "B_АР_ПД.ifc"
            kr = root / "C_КР_ПД.ifc"
            small.write_bytes(b"IFC" + b"0" * 32)
            large.write_bytes(b"IFC" + b"0" * 128)
            kr.write_bytes(b"IFC" + b"0" * 200)
            chosen = pick_primary_ifc([small, large, kr])
            self.assertEqual(chosen, large)

    def test_drawing_limit_and_size_cap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tiny = root / "a.pdf"
            huge = root / "b.pdf"
            tiny.write_bytes(b"%PDF" + b"0" * 10)
            huge.write_bytes(b"%PDF" + b"0" * 80)
            chosen = pick_drawings([tiny, huge], limit=8, max_bytes=50)
            self.assertEqual(chosen, [tiny])

    def test_unsigned_ids_is_allowed(self) -> None:
        path = repo_root() / UNSIGNED_IDS_REL
        self.assertTrue(path.is_file())
        assert_ids_allowed(path)

    def test_rei60_ids_is_forbidden(self) -> None:
        fixture = repo_root() / "samples" / "ids" / "wall-pset-qto.ids"
        with self.assertRaises(ValueError):
            assert_ids_allowed(fixture)


if __name__ == "__main__":
    unittest.main()
