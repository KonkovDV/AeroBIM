"""WP-R3: PDF layers follow HTML order; coverage stays on page 1."""

from __future__ import annotations

import unittest

from test_report_pdf_coverage import extract_pdf_text

from aerobim.presentation.http.report_pdf import render_report_pdf_bytes


class ReportPdfLayerTests(unittest.TestCase):
    def test_pdf_layer_headings_in_order(self) -> None:
        data = {
            "summary": {
                "passed": False,
                "issue_count": 2,
                "error_count": 1,
                "warning_count": 0,
            },
            "issues": [
                {
                    "rule_id": "REQ-FIRE-001",
                    "severity": "error",
                    "message": (
                        "Property Pset_WallCommon.FireRating does not match the expected value"
                    ),
                    "element_guid": "g1",
                    "target_ref": "Wall-01",
                    "evidence_refs": ["guid"],
                    "remark": {
                        "essence": "Стена не соответствует",
                        "clause_cite": "СП 2.13130 п. 5.4.3",
                        "clause_bound": True,
                        "location_line": "этаж 3",
                    },
                },
                {
                    "rule_id": "AEROBIM-SPACE-EFFICIENCY-CANDIDATE",
                    "origin": "advisory",
                    "message": "candidate",
                    "remark": {"essence": "Кандидат площади"},
                },
            ],
            "coverage": {},
        }
        text = extract_pdf_text(render_report_pdf_bytes("r-pdf", data))
        pack = text.find("Замечания к комплекту")
        coverage_notes = text.find("Проверки без объектов проверки")
        service = text.find("Служебные записи")
        advisory = text.find("Кандидаты, требующие согласования критерия")
        self.assertGreater(pack, 0)
        self.assertGreater(coverage_notes, pack)
        self.assertGreater(service, coverage_notes)
        self.assertGreater(advisory, service)

    def test_pdf_first_page_is_coverage_map(self) -> None:
        data = {
            "summary": {"passed": True, "issue_count": 0, "error_count": 0, "warning_count": 0},
            "issues": [],
            "coverage": {},
        }
        text = extract_pdf_text(render_report_pdf_bytes("r-pdf", data))
        self.assertLess(text.find("CHECK COVERAGE MAP"), text.find("Замечания к комплекту"))
        self.assertIn("КРАТКАЯ ВЫЖИМКА", text)

    def test_pdf_extracts_cyrillic_essence(self) -> None:
        data = {
            "summary": {"passed": False, "issue_count": 1, "error_count": 1, "warning_count": 0},
            "issues": [
                {
                    "rule_id": "REQ-FIRE-001",
                    "severity": "error",
                    "message": "mismatch",
                    "element_guid": "g1",
                    "target_ref": "Wall-01",
                    "evidence_refs": ["guid"],
                    "remark": {
                        "essence": "Несущая стена ё не соответствует",
                        "clause_cite": "СП 63",
                        "clause_bound": True,
                        "location_line": "этаж 1",
                    },
                }
            ],
            "coverage": {},
        }
        text = extract_pdf_text(render_report_pdf_bytes("r-cyr", data))
        self.assertIn("ё", text)
        self.assertIn("Несущая стена", text)


if __name__ == "__main__":
    unittest.main()
