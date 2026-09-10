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

from aerobim.domain.executive_brief import executive_brief
from aerobim.domain.finding_layer import (
    FINDING_LAYER_ORDER,
    classify_finding_layer,
    classify_tz_section,
    layer_labels,
    tz_section_labels,
)
from aerobim.domain.remark_completeness import incomplete_marker
from aerobim.domain.review_projection import review_partition_of
from aerobim.presentation.http.report_html import (
    coverage_lines_for_export,
    issue_clause_label,
    issue_display_text,
    issue_location_line,
)

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


def render_report_pdf_bytes(
    report_id: str,
    data: dict[str, Any],
    *,
    locale: str = "ru",
) -> bytes:
    """Build a PDF; page 1 starts with the executive brief, then the coverage map."""

    normalized = "en" if str(locale).strip().lower().startswith("en") else "ru"
    summary: dict[str, Any] = data.get("summary") or {}
    status = "PASSED" if summary.get("passed") else "FAILED"
    labels = layer_labels(normalized)
    tz_labels = tz_section_labels(normalized)
    story: list[Any] = [
        _p(f"AeroBIM Validation Report {report_id}", 12),
        _p(f"Outcome: {status}"),
        _p(
            f"Issues: {summary.get('issue_count', 0)} "
            f"(errors={summary.get('error_count', 0)}, warnings={summary.get('warning_count', 0)})"
        ),
        Spacer(1, 4 * mm),
        *_executive_brief_pdf_blocks(data, locale=normalized),
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
    passport = data.get("run_passport") if isinstance(data.get("run_passport"), dict) else None
    if passport:
        story.append(Spacer(1, 4 * mm))
        story.append(_p("=== RUN PASSPORT (not an SLA) ===", 11))
        story.append(_p(str(passport.get("disclaimer") or "")))
        for stage in passport.get("stages") or ():
            if isinstance(stage, dict):
                story.append(
                    _p(
                        f"{stage.get('name')}: {stage.get('duration_ms')} ms "
                        f"(cumulative {stage.get('cumulative_ms')})"
                    )
                )
        coverage_fmt = (
            passport.get("format_coverage")
            if isinstance(passport.get("format_coverage"), dict)
            else {}
        )
        story.append(
            _p(
                f"formats submitted={coverage_fmt.get('submitted')} "
                f"read={coverage_fmt.get('read')} rejected={coverage_fmt.get('rejected')}"
            )
        )
    calc = (
        data.get("calculation_section")
        if isinstance(data.get("calculation_section"), dict)
        else None
    )
    if calc:
        story.append(Spacer(1, 4 * mm))
        heading = (
            "=== CALCULATION COMPARE (not a solver) ==="
            if normalized == "en"
            else "=== Сверка с расчётом (не пересчёт) ==="
        )
        story.append(_p(heading, 11))
        for row in calc.get("rows") or ():
            if isinstance(row, dict):
                story.append(
                    _p(
                        f"{row.get('id')} {row.get('label')}: "
                        f"{row.get('status')} — {row.get('note')}"
                    )
                )
    story.append(Spacer(1, 4 * mm))
    findings = [issue for issue in (data.get("issues") or []) if isinstance(issue, dict)]
    rejected = [item for item in findings if review_partition_of(item) == "rejected"]
    active = [item for item in findings if review_partition_of(item) != "rejected"]
    for layer in FINDING_LAYER_ORDER:
        bucket = [item for item in active if classify_finding_layer(item) == layer]
        story.append(_p(f"=== {labels[layer]} ({len(bucket)}) ===", 11))
        if not bucket:
            story.append(_p("(empty)"))
            continue
        if layer in {"pack_finding", "advisory_candidate"}:
            for section, section_label in tz_labels.items():
                rows = [item for item in bucket if classify_tz_section(item) == section]
                if not rows:
                    continue
                story.append(_p(f"{section_label} ({len(rows)})", 10))
                for issue in rows:
                    story.extend(_pdf_issue_lines(issue, locale=normalized))
        else:
            for issue in bucket:
                story.extend(_pdf_issue_lines(issue, locale=normalized))
    if rejected:
        heading = "Отклонено экспертом" if normalized != "en" else "Rejected by expert"
        story.append(_p(f"=== {heading} ({len(rejected)}) ===", 11))
        for issue in rejected:
            story.extend(_pdf_issue_lines(issue, locale=normalized))

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


def _executive_brief_pdf_blocks(data: dict[str, Any], *, locale: str) -> list[Any]:
    brief = data.get("executive_brief")
    if not isinstance(brief, dict):
        brief = executive_brief(data)
    heading = "=== EXECUTIVE BRIEF (not accuracy, not SLA) ==="
    if locale != "en":
        heading = "=== КРАТКАЯ ВЫЖИМКА (не точность, не SLA) ==="
    blocks: list[Any] = [
        _p(heading, 11),
        _p(str(brief.get("claim_boundary") or "")),
        _p(
            f"review_mode={brief.get('review_mode')} "
            f"hides_negative={brief.get('hides_negative')} "
            f"is_accuracy={brief.get('is_accuracy')} is_sla={brief.get('is_sla')}"
        ),
        _p(
            f"pack_findings={brief.get('pack_findings')} "
            f"confirmed={brief.get('confirmed')} edited={brief.get('edited')} "
            f"rejected={brief.get('rejected')} unresolved={brief.get('unresolved_review')}"
        ),
        _p(
            f"advisory={brief.get('advisory_candidates')} "
            f"coverage_notes={brief.get('coverage_notes')} "
            f"service={brief.get('service_records')} "
            f"machine={brief.get('machine_records')} "
            f"coverage_not_checked={brief.get('coverage_not_checked')}"
        ),
        _p(
            f"mep_system_clash={brief.get('mep_system_clash')} "
            f"native_dwg={brief.get('native_dwg')} "
            f"calculation_correctness={brief.get('calculation_correctness')} "
            f"run_duration_ms={brief.get('run_duration_ms')}"
        ),
    ]
    for item in brief.get("negative_capabilities") or ():
        if isinstance(item, dict):
            blocks.append(_p(f"capability {item.get('name')}={item.get('status')}"))
    return blocks


def _pdf_issue_lines(issue: dict[str, Any], *, locale: str) -> list[Any]:
    display = issue_display_text(issue)
    clause = issue_clause_label(issue) or ("нет пункта" if locale != "en" else "no clause")
    location = issue_location_line(issue) or "—"
    finding_id = issue.get("finding_id") or ""
    marker = incomplete_marker(issue, locale=locale)
    badge = ""
    state = review_partition_of(issue)
    if state == "confirmed":
        badge = " [подтверждено экспертом]" if locale != "en" else " [confirmed]"
    elif state == "edited":
        badge = " [текст эксперта]" if locale != "en" else " [expert text]"
    lines = [
        _p(
            f"[{issue.get('severity', '?')}] {issue.get('rule_id', '')}: "
            f"{display}{badge} | {clause} | {location} | {finding_id}"
        )
    ]
    if marker:
        lines.append(_p(f"    {marker}"))
    review = issue.get("review")
    machine = str(issue.get("message") or "")
    if isinstance(review, dict) and review.get("machine_text"):
        machine = str(review.get("machine_text") or machine)
        if review.get("effective_text"):
            lines.append(
                _p(f"    review={review.get('state') or '—'}: {review.get('effective_text')}")
            )
    lines.append(_p(f"    machine={machine}"))
    return lines


def render_report_pdf(report_id: str, data: dict[str, Any], out_path: Any) -> None:
    """Write PDF bytes to *out_path* (Path-like)."""

    Path(out_path).write_bytes(render_report_pdf_bytes(report_id, data))
