
"""Unpack census pin stays name-free and is not «processed»."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.unpack_census import (
    PUBLIC_UNPACK_CENSUS,
    unpack_census_snapshot,
)

_REPO = Path(__file__).resolve().parents[2]
_EVIDENCE = _REPO / "docs" / "evidence" / "unpack-census-latest.json"


class UnpackCensusTests(unittest.TestCase):
    def test_snapshot_stays_no_go_and_unprocessed(self) -> None:
        snap = unpack_census_snapshot()
        self.assertEqual(snap["checkpoint"], CHECKPOINT)
        self.assertFalse(snap["processed"])
        self.assertFalse(snap["raise_cap"])
        self.assertFalse(snap["parse_rvt_nwd_lira"])
        self.assertFalse(snap["names_in_git"])
        self.assertFalse(snap["hashes_in_git"])
        self.assertEqual(snap["ifc_schema"], "IFC2X3")
        self.assertEqual(snap["ifc_over_spf_cap_count"], 1)
        self.assertEqual(snap["default_ifc_cap_mib"], 256)
        self.assertGreater(snap["unpacked_file_count"], snap["wrapper_file_count"])
        self.assertGreater(
            snap["wrapper_file_count"], snap["public_rehearsal_file_count_2026_08_27"]
        )
        blob = json.dumps(snap)
        self.assertNotIn("pack_hash", blob)
        self.assertNotIn("sha256", blob)
        self.assertNotIn("43 GB processed", blob)

    def test_pin_counts_are_positive(self) -> None:
        pin = PUBLIC_UNPACK_CENSUS
        self.assertEqual(pin["wrapper_ifc_count"], 15)
        self.assertEqual(pin["unpacked_ifc_count"], 4)
        self.assertEqual(pin["unpacked_pdf_count"], 2046)
        self.assertEqual(pin["unpacked_dwg_count"], 1877)
        self.assertEqual(pin["unpacked_rvt_count"], 75)
        self.assertEqual(pin["wrapper_file_count"], 2552)
        self.assertEqual(pin["unpacked_file_count"], 6408)
        self.assertEqual(pin["unpacked_zip_shells"], 0)
        self.assertEqual(pin["wrapper_zip_count"], 0)
        self.assertTrue(pin["source_archives_deleted_after_coverage"])

    def test_evidence_json_matches_snapshot(self) -> None:
        dumped = json.loads(_EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(dumped, unpack_census_snapshot())


if __name__ == "__main__":
    unittest.main()
