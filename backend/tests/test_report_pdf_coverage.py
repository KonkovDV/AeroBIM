"""WP-R4: PDF export places coverage map on the first page."""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.domain.check_coverage import coverage_from_report
from aerobim.domain.models import (
    ParsedRequirement,
    ValidationReport,
    ValidationSummary,
)
from aerobim.presentation.http.report_pdf import render_report_pdf_bytes


def extract_pdf_text(pdf_bytes: bytes) -> str:
    import pypdfium2 as pdfium

    document = pdfium.PdfDocument(pdf_bytes)
    try:
        chunks: list[str] = []
        for index in range(len(document)):
            page = document[index]
            textpage = page.get_textpage()
            try:
                chunks.append(textpage.get_text_bounded())
            finally:
                textpage.close()
        return "\n".join(chunks)
    finally:
        document.close()


class ReportPdfCoverageTests(unittest.TestCase):
    def test_pdf_starts_with_coverage_block(self) -> None:
        report = ValidationReport(
            report_id="r1",
            request_id="req",
            ifc_path=Path("m.ifc"),
            created_at="2026-08-08T00:00:00Z",
            requirements=(ParsedRequirement(rule_id="r", source="spec.pdf"),),
            issues=(),
            summary=ValidationSummary(
                requirement_count=1,
                issue_count=0,
                error_count=0,
                warning_count=0,
                passed=True,
            ),
        )
        data = {
            "summary": {
                "passed": True,
                "issue_count": 0,
                "error_count": 0,
                "warning_count": 0,
                "requirement_count": 1,
            },
            "issues": [],
            "coverage": coverage_from_report(report).to_dict(report=report),
        }
        pdf = render_report_pdf_bytes("r1", data)
        self.assertTrue(pdf.startswith(b"%PDF"))
        text = extract_pdf_text(pdf)
        self.assertIn("CHECK COVERAGE MAP", text)
        self.assertIn("not_checked", text)
        self.assertIn("MEP", text)

    def test_pdf_keeps_cyrillic_full_finding_text_and_specials(self) -> None:
        long_message = (
            "Несущая стена не соответствует СП 63.13330: класс бетона B25, "
            "арматура Ø12, проём с буквой ё. " + ("длина " * 40)
        )
        specials = r"скобки () слэш \\ углы <> амперсанд &"
        data = {
            "summary": {
                "passed": False,
                "issue_count": 2,
                "error_count": 2,
                "warning_count": 0,
            },
            "issues": [
                {
                    "severity": "error",
                    "category": "ids",
                    "rule_id": "SP-63-1",
                    "message": long_message,
                    "review": {"effective_text": long_message, "state": "edited"},
                },
                {
                    "severity": "error",
                    "category": "ids",
                    "rule_id": "ESC-1",
                    "message": specials,
                },
                *[
                    {
                        "severity": "warning",
                        "category": "ids",
                        "rule_id": f"PAGE-{index}",
                        "message": f"страница многостраничного экспорта {index} ё",
                    }
                    for index in range(60)
                ],
            ],
            "coverage": {},
        }
        pdf = render_report_pdf_bytes("r-cyr", data)
        text = extract_pdf_text(pdf)
        self.assertIn("ё", text)
        self.assertIn("СП 63", text)
        self.assertIn("длина", text)
        self.assertGreater(len(long_message), 120)
        self.assertIn(long_message[:80], text.replace("\n", " "))
        self.assertIn("()", text)
        self.assertIn("<>", text)
        self.assertGreaterEqual(_page_count(pdf), 2)


def _page_count(pdf_bytes: bytes) -> int:
    import pypdfium2 as pdfium

    document = pdfium.PdfDocument(pdf_bytes)
    try:
        return len(document)
    finally:
        document.close()
