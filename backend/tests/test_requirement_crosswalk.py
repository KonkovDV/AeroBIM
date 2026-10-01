"""WP-R19: requirement crosswalk is coverage, not TP/FP; no auto-match."""

from __future__ import annotations

import unittest

from aerobim.domain.requirement_crosswalk import build_requirement_crosswalk


class RequirementCrosswalkTests(unittest.TestCase):
    def test_three_numbers_are_named_as_coverage(self) -> None:
        payload = build_requirement_crosswalk(
            [
                {
                    "row_id": "a",
                    "machine_verifiability": "machine_full",
                    "assigned_by": "human",
                    "coverage_status": "checked",
                },
                {
                    "row_id": "b",
                    "machine_verifiability": "needs_document",
                    "assigned_by": "human",
                    "coverage_status": "not_checked",
                },
                {
                    "row_id": "c",
                    "machine_verifiability": "machine_partial",
                    "assigned_by": "human",
                    "coverage_status": "checked",
                },
            ]
        )
        totals = payload["totals"]
        self.assertEqual(totals["requirement_rows"], 3)
        self.assertEqual(totals["machine_verifiable"], 2)
        self.assertEqual(totals["closed_by_run"], 2)
        self.assertFalse(payload["is_accuracy"])
        self.assertIn("не точность", payload["agreement"]["label"])

    def test_llm_rows_excluded_from_denominator(self) -> None:
        payload = build_requirement_crosswalk(
            [
                {
                    "row_id": "llm",
                    "machine_verifiability": "machine_full",
                    "assigned_by": "llm",
                    "coverage_status": "checked",
                }
            ]
        )
        self.assertEqual(payload["totals"]["requirement_rows"], 0)

    def test_matched_finding_ids_stay_empty(self) -> None:
        payload = build_requirement_crosswalk(
            [
                {
                    "row_id": "a",
                    "machine_verifiability": "machine_full",
                    "assigned_by": "human",
                    "coverage_status": "checked",
                    "matched_finding_ids": ["fid-1"],
                }
            ]
        )
        self.assertEqual(payload["rows"][0]["matched_finding_ids"], [])
        self.assertFalse(payload["auto_match"])
        self.assertFalse(payload["publishable"])


if __name__ == "__main__":
    unittest.main()
