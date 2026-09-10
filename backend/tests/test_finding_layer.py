"""WP-R1: presentation layer is grouping, not a verdict."""

from __future__ import annotations

import unittest

from aerobim.domain.finding_layer import (
    FINDING_LAYER_ORDER,
    classify_finding_layer,
    classify_tz_section,
    layer_counts,
)
from aerobim.domain.finding_volume import classify_volume_record
from aerobim.domain.target_ref import UNRESTRICTED_MISMATCH_SUPPRESSOR_MARKER


def _volume_fixtures() -> dict[str, dict[str, object]]:
    return {
        "advisory_unsigned": {
            "rule_id": "AEROBIM-SPACE-EFFICIENCY-CANDIDATE",
            "origin": "advisory",
            "message": "candidate",
        },
        "service_hitl": {"rule_id": "AEROBIM-DRAWING-REGION-HITL", "message": "region"},
        "service_capability": {"rule_id": "AEROBIM-CLASH-CAPABILITY", "message": "cap"},
        "entity_presence": {
            "rule_id": "REQ-FIRE-001",
            "message": "No elements found for entity IFCWALL",
        },
        "coverage_unsigned": {"rule_id": "SAM-AR-001", "message": "coverage"},
        "unrestricted_eq_sample": {
            "rule_id": "REQ-FIRE-001",
            "element_guid": "wall-guid-1",
            "message": "Property Pset_WallCommon.FireRating does not match the expected value",
        },
        "element_detection_unsigned": {
            "rule_id": "REQ-FIRE-001",
            "target_ref": "Wall-01",
            "element_guid": "wall-guid-1",
            "message": "Property Pset_WallCommon.FireRating does not match the expected value",
        },
        "unsigned_universal_rule": {"rule_id": "REQ-FIRE-001"},
        "data_integrity": {
            "rule_id": "AEROBIM-GUID-DUPLICATE",
            "element_guid": "dup-guid",
            "message": "duplicate",
        },
        "engine_record": {
            "rule_id": "AEROBIM-LOAD-FORMAT",
            "message": "Calculation source present but no LOAD rows matched",
        },
    }


class FindingLayerTests(unittest.TestCase):
    def test_every_volume_class_maps_to_a_layer(self) -> None:
        for volume, item in _volume_fixtures().items():
            self.assertEqual(classify_volume_record(item), volume, volume)
            layer = classify_finding_layer(item)
            self.assertIn(layer, FINDING_LAYER_ORDER, volume)

    def test_advisory_origin_is_candidate(self) -> None:
        self.assertEqual(
            classify_finding_layer({"origin": "advisory", "rule_id": "X", "message": "n"}),
            "advisory_candidate",
        )

    def test_hitl_and_capability_are_service(self) -> None:
        self.assertEqual(
            classify_finding_layer({"rule_id": "AEROBIM-DRAWING-REGION-HITL"}),
            "service_record",
        )
        self.assertEqual(
            classify_finding_layer({"rule_id": "AEROBIM-IDS-CAPABILITY"}),
            "service_record",
        )

    def test_no_elements_found_is_coverage_note(self) -> None:
        self.assertEqual(
            classify_finding_layer(
                {"rule_id": "REQ-FIRE-001", "message": "No elements found for entity IFCWALL"}
            ),
            "coverage_note",
        )

    def test_load_format_record_without_object_is_coverage_note(self) -> None:
        item = {
            "rule_id": "AEROBIM-LOAD-FORMAT",
            "message": "Calculation source present but no LOAD rows matched",
        }
        self.assertEqual(classify_volume_record(item), "engine_record")
        self.assertEqual(classify_finding_layer(item), "coverage_note")

    def test_engine_record_with_guid_and_clause_is_pack_finding(self) -> None:
        item = {
            "rule_id": "AEROBIM-LOAD-FORMAT",
            "element_guid": "guid-load-1",
            "norm_clause": "СП 20 п. 6.1",
            "message": "Calculation source present but no LOAD rows matched",
        }
        self.assertEqual(classify_finding_layer(item), "pack_finding")

    def test_unknown_class_uses_positive_criteria(self) -> None:
        with_object = {
            "rule_id": "FUTURE-ENGINE-X",
            "problem_zone": {"sheet_id": "A-101"},
            "norm_clause": "п. 4.4",
            "message": "engine note",
        }
        self.assertEqual(classify_volume_record(with_object), "engine_record")
        self.assertEqual(classify_finding_layer(with_object), "pack_finding")
        without = {"rule_id": "FUTURE-ENGINE-X", "message": "engine note"}
        self.assertEqual(classify_volume_record(without), "engine_record")
        self.assertEqual(classify_finding_layer(without), "coverage_note")

    def test_layer_does_not_touch_severity_or_priority(self) -> None:
        item = {
            "rule_id": "REQ-FIRE-001",
            "severity": "error",
            "priority": 40,
            "target_ref": "Wall-01",
            "element_guid": "g1",
            "message": "Property Pset_WallCommon.FireRating does not match the expected value",
        }
        snapshot = dict(item)
        classify_finding_layer(item)
        self.assertEqual(item["severity"], snapshot["severity"])
        self.assertEqual(item["priority"], snapshot["priority"])
        self.assertEqual(item, snapshot)

    def test_layer_counts_cover_all_layers(self) -> None:
        counts = layer_counts(list(_volume_fixtures().values()))
        self.assertEqual(set(counts), set(FINDING_LAYER_ORDER))
        self.assertEqual(sum(counts.values()), len(_volume_fixtures()))

    def test_space_efficiency_is_named_tz_section(self) -> None:
        self.assertEqual(
            classify_tz_section({"rule_id": "AEROBIM-SPACE-EFFICIENCY-CANDIDATE"}),
            "space_efficiency",
        )

    def test_suppressed_mismatch_stays_coverage(self) -> None:
        item = {
            "rule_id": "REQ-FIRE-001",
            "message": (
                f"12 further IFCWALL property mismatches "
                f"{UNRESTRICTED_MISMATCH_SUPPRESSOR_MARKER} 50; "
                "not a customer defect list)"
            ),
        }
        self.assertEqual(classify_finding_layer(item), "coverage_note")


if __name__ == "__main__":
    unittest.main()
