"""PDF rendering for report export (WP-R4: coverage map on first page)."""

from __future__ import annotations

from typing import Any

from aerobim.core.simple_pdf import write_simple_pdf
from aerobim.presentation.http.report_html import coverage_lines_for_export, issue_clause_label


def render_report_pdf_bytes(report_id: str, data: dict[str, Any]) -> bytes:
    """Build a minimal PDF; page 1 is the coverage map, then summary + issues."""

    summary: dict[str, Any] = data.get("summary") or {}
    status = "PASSED" if summary.get("passed") else "FAILED"
    lines: list[str] = [
        f"AeroBIM Validation Report {report_id}",
        f"Outcome: {status}",
        f"Issues: {summary.get('issue_count', 0)} "
        f"(errors={summary.get('error_count', 0)}, warnings={summary.get('warning_count', 0)})",
        "",
        "=== CHECK COVERAGE MAP (page 1) ===",
        "'no findings' != 'not checked'. Verdict-neutral observability.",
        "",
    ]
    lines.extend(coverage_lines_for_export(data.get("coverage") or {}))
    lines.extend(
        [
            "",
            "=== FINDINGS (summary) ===",
        ]
    )
    for issue in data.get("issues") or []:
        if not isinstance(issue, dict):
            continue
        clause = issue_clause_label(issue) or "нет пункта"
        lines.append(
            f"[{issue.get('severity', '?')}] {issue.get('category', '?')}: "
            f"{issue.get('rule_id', '')} — {str(issue.get('message', ''))[:120]} | {clause}"
        )
    if len(lines) < 8:
        lines.append("(no issues)")
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "report.pdf"
        write_simple_pdf(path, lines, lines_per_page=45)
        return path.read_bytes()


def render_report_pdf(report_id: str, data: dict[str, Any], out_path: Any) -> None:
    """Write PDF bytes to *out_path* (Path-like)."""

    from pathlib import Path

    Path(out_path).write_bytes(render_report_pdf_bytes(report_id, data))
