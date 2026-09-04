
"""Unsigned educational packs overlap on the same IFC property."""

from __future__ import annotations

import unittest

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.unsigned_rule_overlap import (
    active_overlap_groups,
    normalize_ifc_entity,
    overlap_groups,
    overlap_snapshot,
    property_key,
)


class UnsignedRuleOverlapTests(unittest.TestCase):
    def test_entity_tokens_normalize(self) -> None:
        self.assertEqual(normalize_ifc_entity("IfcWall"), "IFCWALL")
        self.assertEqual(normalize_ifc_entity("IFCWALL"), "IFCWALL")
        self.assertEqual(
            property_key("IfcWall", "Pset_WallCommon", "FireRating"),
            ("IFCWALL", "Pset_WallCommon", "FireRating"),
        )

    def test_fire_eq_and_ar_exists_share_wall_firerating(self) -> None:
        groups = overlap_groups()
        self.assertGreaterEqual(len(groups), 6)
        wall_fire = next(
            item
            for item in groups
            if item["ifc_entity"] == "IFCWALL"
            and item["property_set"] == "Pset_WallCommon"
            and item["property_name"] == "FireRating"
        )
        self.assertIn("REQ-FIRE-001", wall_fire["rule_ids"])
        self.assertIn("SAM-AR-011", wall_fire["rule_ids"])
        snap = overlap_snapshot()
        self.assertEqual(snap["checkpoint"], CHECKPOINT)
        self.assertFalse(snap["is_accuracy"])
        self.assertFalse(snap["is_customer_defect_list"])
        self.assertEqual(snap["group_count"], len(groups))

    def test_active_groups_need_two_present_rules(self) -> None:
        self.assertEqual(active_overlap_groups(["REQ-FIRE-001"]), [])
        active = active_overlap_groups(["REQ-FIRE-001", "SAM-AR-011"])
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["property_name"], "FireRating")


if __name__ == "__main__":
    unittest.main()
