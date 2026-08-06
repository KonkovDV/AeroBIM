from __future__ import annotations

import unittest

from aerobim.domain.documentation_standard_edition import (
    load_selection_rule,
    select_documentation_standard_edition,
)
from aerobim.domain.package_completeness import PackageInventory


class DocumentationStandardEditionTests(unittest.TestCase):
    def test_explicit_wins(self) -> None:
        edition, source = select_documentation_standard_edition(
            package_developed_on="2025-01-01",
            explicit_edition="21.101-2026",
            rule={
                "cutoff_exclusive": "2026-04-01",
                "before_cutoff": "21.101-2020",
                "on_or_after_cutoff": "21.101-2026",
            },
        )
        self.assertEqual(edition, "21.101-2026")
        self.assertEqual(source, "explicit_inventory_field")

    def test_cutoff_before_and_after(self) -> None:
        rule = {
            "cutoff_exclusive": "2026-04-01",
            "before_cutoff": "21.101-2020",
            "on_or_after_cutoff": "21.101-2026",
        }
        before, src_b = select_documentation_standard_edition(
            package_developed_on="2026-03-31", rule=rule
        )
        after, src_a = select_documentation_standard_edition(
            package_developed_on="2026-04-01", rule=rule
        )
        self.assertEqual(before, "21.101-2020")
        self.assertEqual(after, "21.101-2026")
        self.assertIn("before", src_b)
        self.assertIn("on_or_after", src_a)

    def test_inventory_applies_rule(self) -> None:
        inv = PackageInventory.from_mapping(
            {
                "schema": "aerobim_package_inventory_v1",
                "project_id": "t",
                "package_developed_on": "2026-05-01",
                "documentation_standard_selection_rule": {
                    "cutoff_exclusive": "2026-04-01",
                    "before_cutoff": "21.101-2020",
                    "on_or_after_cutoff": "21.101-2026",
                },
                "artifacts": [],
            }
        )
        self.assertEqual(inv.documentation_standard_edition, "21.101-2026")
        self.assertIsNotNone(load_selection_rule({"selection_rule": {"cutoff_exclusive": "x"}}))


if __name__ == "__main__":
    unittest.main()
