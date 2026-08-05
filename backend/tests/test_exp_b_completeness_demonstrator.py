"""Exp B completeness demonstrator — KR 25pp rows vs existing WP-05 / section-diff.

No new ports. Proves which «package completeness» conditional rows actually fire
on open/synthetic packages (AUTHOR_CLAIM coverage map update input).
"""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.domain.package_completeness import assess_package_completeness
from aerobim.infrastructure.adapters.json_package_inventory_loader import (
    JsonPackageInventoryLoader,
)
from aerobim.infrastructure.adapters.json_section_diff_analyzer import JsonSectionDiffAnalyzer

REPO = Path(__file__).resolve().parents[2]
PACKAGES = REPO / "samples" / "packages"
SECTIONS = REPO / "samples" / "sections"


class ExpBCompletenessDemonstratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.loader = JsonPackageInventoryLoader()

    def test_kr24_missing_kzh_fires_missing_section(self) -> None:
        """KR #24 opener «оба раздела» → MISSING-SECTION when KZH absent."""
        inv = self.loader.load(PACKAGES / "residential-missing-kzh-inventory.json")
        report = assess_package_completeness(inv)
        rule_ids = {i.rule_id for i in report.issues}
        self.assertIn("AEROBIM-PACKAGE-MISSING-SECTION", rule_ids)
        self.assertIn("KZH", report.missing_pd_sections)

    def test_kr24_complete_package_has_ar_and_kzh(self) -> None:
        inv = self.loader.load(PACKAGES / "residential-complete-inventory.json")
        report = assess_package_completeness(inv)
        self.assertEqual(report.issues, ())
        self.assertEqual(report.missing_pd_sections, ())

    def test_kr3_kzh_section_diff_fires_without_customer_norms(self) -> None:
        """KR #3 class: PD/RD section value mismatches on synthetic KZH (no RT-002)."""
        analyzer = JsonSectionDiffAnalyzer()
        pairing = analyzer.analyze(
            SECTIONS / "kzh-pd-synthetic.json",
            SECTIONS / "kzh-rd-synthetic.json",
        )
        self.assertGreaterEqual(len(pairing.issues), 1)
        self.assertTrue(
            any("SECTION-PAIR-KZH" in i.rule_id for i in pairing.issues),
            msg=[i.rule_id for i in pairing.issues],
        )

    def test_orphan_calc_in_inventory_does_not_imply_unjustified_calc_rule(self) -> None:
        """KR #4: declaring calculation in inventory ≠ runtime «unjustified in PD» check."""
        inv = self.loader.load(PACKAGES / "residential-missing-kzh-inventory.json")
        report = assess_package_completeness(inv)
        rule_ids = {i.rule_id for i in report.issues}
        self.assertNotIn("AEROBIM-PACKAGE-UNJUSTIFIED-CALCULATION", rule_ids)


if __name__ == "__main__":
    unittest.main()
