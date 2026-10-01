"""Seam-clean wall+IDS targeted injection recall (10 trials)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.tools.evaluate_injection_recall import targeted_issue_key
from aerobim.tools.run_seam_clean_injection_recall import (
    MUTATIONS,
    WALL_GUID,
    evaluate_seam_clean_tree,
    write_seam_clean_tree,
)

_REPO = Path(__file__).resolve().parents[2]
_IFC = _REPO / "samples" / "ifc" / "wall-fire-rating-rei60.ifc"
_IDS = _REPO / "samples" / "ids" / "wall-fire-rating.ids"


class SeamCleanInjectionRecallTests(unittest.TestCase):
    def test_ten_mutations_and_targeted_key_shape(self) -> None:
        self.assertEqual(len(MUTATIONS), 10)
        key = targeted_issue_key(
            {
                "rule_id": "IDS-Wall Fire Rating",
                "element_guid": WALL_GUID,
                "norm_clause": "",
                "target_ref": "Wall Fire Rating",
                "observed_value": "REI45",
            }
        )
        self.assertEqual(key[0], "IDS-Wall Fire Rating")
        self.assertEqual(key[1], WALL_GUID)

    def test_live_contour_kills_at_least_nine_of_ten(self) -> None:
        with tempfile.TemporaryDirectory(prefix="aerobim-seam-test-") as tmp:
            root = Path(tmp)
            manifest = write_seam_clean_tree(root=root / "injected", source_ifc=_IFC)
            artifact = evaluate_seam_clean_tree(
                injection_root=root / "injected",
                manifest_path=manifest,
                ids_path=_IDS,
                storage_dir=root / "var",
            )
        self.assertEqual(artifact["control_issue_count"], 0)
        self.assertGreaterEqual(artifact["aggregate"]["trials"], 10)
        self.assertGreaterEqual(artifact["aggregate"]["killed"], 9)
        self.assertFalse(artifact["closes_rt001"])
        self.assertFalse(artifact["customer_go"])
        self.assertIn("seam-clean", artifact["plan_deviation"])


if __name__ == "__main__":
    unittest.main()
