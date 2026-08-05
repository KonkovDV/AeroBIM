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

    def test_kr4_unjustified_calc_in_pd_fires(self) -> None:
        """KR #4 LOGIC_ABSENT closed: PD calculation without justification marker."""
        inv = self.loader.load(PACKAGES / "residential-unjustified-calc-pd-inventory.json")
        report = assess_package_completeness(inv)
        rule_ids = {i.rule_id for i in report.issues}
        self.assertIn("AEROBIM-PACKAGE-UNJUSTIFIED-CALCULATION", rule_ids)

    def test_kr2_technical_spec_missing_floor_partition_topics_fires(self) -> None:
        """KR #2 LOGIC_ABSENT closed: ТЧ present but floors/partitions topics absent."""
        inv = self.loader.load(PACKAGES / "residential-tech-spec-missing-topics-inventory.json")
        report = assess_package_completeness(inv)
        rule_ids = {i.rule_id for i in report.issues}
        self.assertIn("AEROBIM-PACKAGE-TECHNICAL-SPEC-MISSING-TOPIC", rule_ids)

    def test_orphan_calc_on_missing_kzh_also_fires_unjustified(self) -> None:
        """Same KR #4 rule applies when calc is declared on incomplete packages."""
        inv = self.loader.load(PACKAGES / "residential-missing-kzh-inventory.json")
        report = assess_package_completeness(inv)
        rule_ids = {i.rule_id for i in report.issues}
        self.assertIn("AEROBIM-PACKAGE-UNJUSTIFIED-CALCULATION", rule_ids)
        self.assertIn("AEROBIM-PACKAGE-MISSING-SECTION", rule_ids)


if __name__ == "__main__":
    unittest.main()
