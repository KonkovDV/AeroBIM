
"""Deep-study carrier pin stays name-free and is not «processed»."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.deep_study_facts import (
    PUBLIC_DEEP_STUDY,
    deep_study_snapshot,
)

_REPO = Path(__file__).resolve().parents[2]
_EVIDENCE = _REPO / "docs" / "evidence" / "deep-study-carrier-facts-latest.json"


class DeepStudyFactsTests(unittest.TestCase):
    def test_snapshot_stays_no_go_and_unprocessed(self) -> None:
        snap = deep_study_snapshot()
        self.assertEqual(snap["checkpoint"], CHECKPOINT)
        self.assertFalse(snap["processed"])
        self.assertFalse(snap["raise_cap"])
        self.assertFalse(snap["parse_rvt_nwd_lira"])
        self.assertFalse(snap["names_in_git"])
        self.assertFalse(snap["hashes_in_git"])
        self.assertFalse(snap["customer_approved_ids"])
        self.assertTrue(snap["eir_v4_present"])
        self.assertTrue(snap["bim_standard_v4_present"])
        self.assertTrue(snap["eir_lod_mep_disciplines_named"])
        self.assertEqual(snap["nwd_federation_count"], 3)
        self.assertEqual(snap["customer_confirmed_patterns"], 0)
        self.assertEqual(snap["ifc_schema"], "IFC2X3")
        self.assertEqual(snap["netfloorarea_count"], 0)
        self.assertEqual(snap["ifcreinforcingbar_count"], 0)
        self.assertEqual(snap["mep_duct_pipe_cable_count"], 0)
        self.assertEqual(snap["ifcgrid_pack_a"], 0)
        self.assertEqual(snap["default_ifc_cap_mib"], 256)
        blob = json.dumps(snap)
        self.assertNotIn("pack_hash", blob)
        self.assertNotIn("sha256", blob)
        self.assertNotIn('processed": true', blob.replace(" ", ""))

    def test_pin_counts_match_evening_pass(self) -> None:
        pin = PUBLIC_DEEP_STUDY
        self.assertEqual(pin["unique_ifc_count"], 15)
        self.assertEqual(pin["ifcspace_pack_a"], 10599)
        self.assertEqual(pin["ifcwall_pack_a"], 62033)
        self.assertEqual(pin["unique_pdf_count"], 1440)
        self.assertEqual(pin["unique_rvt_count"], 87)
        self.assertEqual(pin["rvt_2020_count"] + pin["rvt_2023_count"], 87)
        self.assertFalse(pin["lira_present_pack_b"])

    def test_evidence_json_matches_snapshot(self) -> None:
        dumped = json.loads(_EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(dumped, deep_study_snapshot())


if __name__ == "__main__":
    unittest.main()
