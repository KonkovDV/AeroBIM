"""PDF rendering for report export (WP-R4: coverage map on first page).

Uses ReportLab + a vendored OFL Liberation Sans TTF so Cyrillic findings are
extractable. Not a custom Unicode PDF engine. Font is shipped in-tree; no
runtime download. PyMuPDF stays optional ``pdf-agpl`` only.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from aerobim.presentation.http.report_html import coverage_lines_for_export, issue_clause_label

_FONT_NAME = "LiberationSans"
_FONT_REGISTERED = False
_FONT_PATH = Path(__file__).resolve().parent / "fonts" / "LiberationSans-Regular.ttf"


def _register_export_font() -> str:
    global _FONT_REGISTERED
    if not _FONT_REGISTERED:
        if not _FONT_PATH.is_file():
            raise FileNotFoundError(f"Vendored export font missing: {_FONT_PATH}")
        pdfmetrics.registerFont(TTFont(_FONT_NAME, str(_FONT_PATH)))
        _FONT_REGISTERED = True
    return _FONT_NAME


def _style(size: float, *, leading: float | None = None) -> ParagraphStyle:
    font = _register_export_font()
    return ParagraphStyle(
        name=f"aerobim-export-{size}",
        fontName=font,
        fontSize=size,
        leading=leading or size + 3,
        spaceAfter=2,
    )


def _p(text: str, size: float = 9) -> Paragraph:
    return Paragraph(escape(text).replace("\n", "<br/>"), _style(size))


def render_report_pdf_bytes(report_id: str, data: dict[str, Any]) -> bytes:
    """Build a PDF; page 1 starts with the coverage map, then summary + full findings."""

    summary: dict[str, Any] = data.get("summary") or {}
    status = "PASSED" if summary.get("passed") else "FAILED"
    story: list[Any] = [
        _p(f"AeroBIM Validation Report {report_id}", 12),
        _p(f"Outcome: {status}"),
        _p(
            f"Issues: {summary.get('issue_count', 0)} "
            f"(errors={summary.get('error_count', 0)}, warnings={summary.get('warning_count', 0)})"
        ),
        Spacer(1, 4 * mm),
        _p("=== CHECK COVERAGE MAP (page 1) ===", 11),
        _p("'no findings' != 'not checked'. Verdict-neutral observability."),
        Spacer(1, 2 * mm),
    ]
    coverage_lines = coverage_lines_for_export(data.get("coverage") or {})
    if not coverage_lines:
        story.append(_p("(no coverage data)"))
    else:
        for line in coverage_lines:
            story.append(_p(line if line else " "))
    story.append(Spacer(1, 4 * mm))
    story.append(_p("=== FINDINGS (summary) ===", 11))
    findings = [issue for issue in (data.get("issues") or []) if isinstance(issue, dict)]
    if not findings:
        story.append(_p("(no issues)"))
    for issue in findings:
        clause = issue_clause_label(issue) or "нет пункта"
        story.append(
            _p(
                f"[{issue.get('severity', '?')}] {issue.get('category', '?')}: "
                f"{issue.get('rule_id', '')} — {issue.get('message', '')} | {clause}"
            )
        )
        review = issue.get("review")
        if isinstance(review, dict):
            effective = review.get("effective_text")
            if effective:
                state = review.get("state") or "—"
                story.append(_p(f"    review={state}: {effective}"))
            machine = review.get("machine_text")
            if machine and machine != effective:
                story.append(_p(f"    machine={machine}"))

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"AeroBIM {report_id}",
    )
    document.build(story)
    return buffer.getvalue()


def render_report_pdf(report_id: str, data: dict[str, Any], out_path: Any) -> None:
    """Write PDF bytes to *out_path* (Path-like)."""

    Path(out_path).write_bytes(render_report_pdf_bytes(report_id, data))
