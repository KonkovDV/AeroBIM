"""WP-R13: four calculation rows always present; absent rebar is no-data."""

from __future__ import annotations

import unittest

from aerobim.domain.calculation_report_section import calculation_section
from aerobim.presentation.http.report_html import render_report_html


class CalculationSectionTests(unittest.TestCase):
    def test_four_rows_always_present_with_explicit_status(self) -> None:
        section = calculation_section(reinforcing_bar_count=0)
        self.assertEqual(len(section["rows"]), 4)
        self.assertEqual({row["id"] for row in section["rows"]}, {"CC-1", "CC-2", "CC-3", "CC-4"})
        for row in section["rows"]:
            self.assertIn(row["status"], {"сверено", "нет данных в комплекте", "не поддержано"})

    def test_absent_rebar_yields_no_data_not_silence(self) -> None:
        section = calculation_section(reinforcing_bar_count=0)
        rebar = next(row for row in section["rows"] if row["id"] == "CC-1")
        self.assertEqual(rebar["status"], "нет данных в комплекте")
        html = render_report_html(
            "r" * 32,
            {
                "summary": {
                    "passed": False,
                    "issue_count": 0,
                    "error_count": 0,
                    "warning_count": 0,
                    "requirement_count": 0,
                },
                "issues": [],
                "calculation_section": section,
            },
        )
        self.assertIn("IfcReinforcingBar", html)
        self.assertIn("нет данных", html)

    def test_export_path_without_count_does_not_claim_zero_bars(self) -> None:
        section = calculation_section()
        rebar = next(row for row in section["rows"] if row["id"] == "CC-1")
        self.assertEqual(rebar["status"], "нет данных в комплекте")
        self.assertNotIn("= 0", rebar["note"])
        self.assertIn("not counted", rebar["note"])

    def test_section_states_no_independent_recalculation(self) -> None:
        section = calculation_section()
        self.assertFalse(section["independent_recalculation"])
        html = render_report_html(
            "r" * 32,
            {
                "summary": {
                    "passed": False,
                    "issue_count": 0,
                    "error_count": 0,
                    "warning_count": 0,
                    "requirement_count": 0,
                },
                "issues": [],
                "calculation_section": section,
            },
        )
        self.assertIn("независимый пересчёт", html.lower())


if __name__ == "__main__":
    unittest.main()
