"""WP-R10: 2.1.5 triad completeness is coverage, not accuracy."""

from __future__ import annotations

import unittest

from aerobim.domain.remark_completeness import (
    completeness_table,
    incomplete_marker,
    remark_completeness,
)
from aerobim.domain.remark_shape import UNBOUND_CLAUSE_RU


class RemarkCompletenessTests(unittest.TestCase):
    def test_unbound_clause_marker_counts_as_missing(self) -> None:
        flags = remark_completeness(
            {
                "rule_id": "REQ-FIRE-001",
                "element_guid": "g1",
                "target_ref": "Wall-01",
                "message": "mismatch",
                "remark": {
                    "essence": "Стена не соответствует",
                    "clause_cite": UNBOUND_CLAUSE_RU,
                    "clause_bound": False,
                    "location_line": "этаж 3; ось А",
                },
            }
        )
        self.assertFalse(flags["has_clause"])
        self.assertTrue(flags["has_essence"])
        self.assertTrue(flags["has_location"])
        self.assertFalse(flags["full_triad"])

    def test_full_triad_requires_essence_clause_location(self) -> None:
        flags = remark_completeness(
            {
                "rule_id": "REQ-FIRE-001",
                "element_guid": "g1",
                "target_ref": "Wall-01",
                "message": "mismatch",
                "norm_clause": "8.1",
                "remark": {
                    "essence": "Стена не соответствует REI 60",
                    "clause_cite": "СП 2.13130 п. 5.4.3",
                    "clause_bound": True,
                    "location_line": "этаж 3; ось А; GUID g1",
                },
            }
        )
        self.assertTrue(flags["full_triad"])
        self.assertTrue(flags["has_object"])

    def test_table_is_marked_not_accuracy(self) -> None:
        table = completeness_table(
            [
                {
                    "rule_id": "REQ-FIRE-001",
                    "element_guid": "g1",
                    "target_ref": "Wall-01",
                    "message": (
                        "Property Pset_WallCommon.FireRating does not match the expected value"
                    ),
                    "remark": {
                        "essence": "Стена не соответствует",
                        "clause_cite": "СП 2.13130 п. 5.4.3",
                        "clause_bound": True,
                        "location_line": "этаж 3",
                    },
                },
                {
                    "rule_id": "AEROBIM-CLASH-CAPABILITY",
                    "message": "cap",
                },
            ]
        )
        self.assertFalse(table["is_accuracy"])
        self.assertEqual(table["claim_level"], "coverage_map_only")
        self.assertEqual(table["pack_finding_count"], 1)
        self.assertEqual(table["full_triad_count"], 1)

    def test_incomplete_rows_are_marked_in_export(self) -> None:
        item = {
            "rule_id": "REQ-FIRE-001",
            "element_guid": "g1",
            "message": "mismatch",
            "remark": {
                "essence": "Стена",
                "clause_cite": UNBOUND_CLAUSE_RU,
                "clause_bound": False,
                "location_line": "без точной привязки",
            },
        }
        marker = incomplete_marker(item, locale="ru")
        self.assertIn("неполное замечание", marker)
        self.assertIn("нет пункта", marker)
        self.assertIn("нет локации", marker)
        from aerobim.presentation.http.report_html import render_report_html

        html = render_report_html(
            "r" * 32,
            {
                "summary": {
                    "passed": False,
                    "issue_count": 1,
                    "error_count": 1,
                    "warning_count": 0,
                    "requirement_count": 0,
                },
                "issues": [
                    {
                        **item,
                        "target_ref": "Wall-01",
                        "evidence_refs": ["g1"],
                    }
                ],
            },
        )
        self.assertIn("неполное замечание", html)
        self.assertEqual(
            incomplete_marker(
                {
                    **item,
                    "remark": {
                        "essence": "Стена",
                        "clause_cite": "СП 2.13130 п. 5.4.3",
                        "clause_bound": True,
                        "location_line": "этаж 3",
                    },
                },
                locale="ru",
            ),
            "",
        )


if __name__ == "__main__":
    unittest.main()
