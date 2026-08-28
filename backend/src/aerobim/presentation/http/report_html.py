"""HTML rendering for report export (extracted from api.py).

Pure string rendering: takes the already-serialized public report payload and
returns a standalone HTML document. No FastAPI / auth concerns here.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def _esc(value: str) -> str:
    """HTML-escape user-controlled values for element text and attributes."""
    import html

    return html.escape(str(value), quote=True)


_TRIAGE_BANDS = ("critical", "major", "minor", "negligible")


def _triage_band(issue: dict[str, Any]) -> str | None:
    """Deterministic clash triage band carried in evidence_refs (Wave B)."""
    refs = issue.get("evidence_refs") or ()
    if not isinstance(refs, list | tuple):
        return None
    for ref in refs:
        text = str(ref)
        if text.startswith("triage:band="):
            band = text.removeprefix("triage:band=")
            if band in _TRIAGE_BANDS:
                return band
    return None


def _build_issue_rows(issues: list[dict[str, Any]]) -> str:
    rows = ""
    sorted_issues = sorted(issues, key=lambda i: i.get("priority", 0), reverse=True)
    for issue in sorted_issues:
        sev = issue.get("severity", "")
        exp = issue.get("expected_value", "")
        obs = issue.get("observed_value", "")
        unit = issue.get("unit", "")
        pz = issue.get("problem_zone")
        pz_html = ""
        if pz:
            sheet = _esc(pz.get("sheet_id") or "")
            x = pz.get("x")
            y = pz.get("y")
            if sheet and x is not None and y is not None:
                pz_html = f"<br><small class='pz'>Лист: {sheet} ({x:.1f}, {y:.1f})</small>"
        ev_obs = (
            f"<td>{_esc(obs)}{_esc(' ' + unit if unit and obs else '')}</td>"
            if obs
            else "<td>—</td>"
        )
        ev_exp = (
            f"<td>{_esc(exp)}{_esc(' ' + unit if unit and exp else '')}</td>"
            if exp
            else "<td>—</td>"
        )
        pri = issue.get("priority", 0)
        pri_class = "pri-high" if pri >= 45 else "pri-med" if pri >= 25 else "pri-low"
        band = _triage_band(issue)
        band_html = f" <span class='band band-{band}'>{_esc(band)}</span>" if band else ""
        conf = issue.get("confidence")
        conf_display = f"{conf:.2f}" if conf is not None else "—"
        loin_bits = []
        for key, label in (
            ("loin_purpose", "purpose"),
            ("loin_milestone", "milestone"),
            ("loin_actor", "actor"),
            ("loin_information_level", "level"),
        ):
            value = issue.get(key)
            if value:
                loin_bits.append(f"{label}={_esc(str(value))}")
        loin_html = f"<br><small class='loin'>{' · '.join(loin_bits)}</small>" if loin_bits else ""
        norm_bits: list[str] = []
        approval = issue.get("approval_status")
        if approval:
            norm_bits.append(f"badge={_esc(str(approval))}")
        for key, label in (
            ("norm_source", "src"),
            ("norm_edition", "ed"),
            ("norm_clause", "§"),
            ("approval_ref", "ref"),
        ):
            value = issue.get(key)
            if value:
                norm_bits.append(f"{label}={_esc(str(value))}")
        norm_html = (
            f"<br><small class='norm-badge'>{' · '.join(norm_bits)}</small>" if norm_bits else ""
        )
        finding_id = issue.get("finding_id") or ""
        source_id = issue.get("source_id") or ""
        evidence_refs = issue.get("evidence_refs") or ()
        if isinstance(evidence_refs, list | tuple):
            refs_joined = ", ".join(str(ref) for ref in evidence_refs if ref)
        else:
            refs_joined = str(evidence_refs)
        audit_bits: list[str] = []
        if finding_id:
            audit_bits.append(f"finding_id={_esc(str(finding_id))}")
        if source_id:
            audit_bits.append(f"source_id={_esc(str(source_id))}")
        if refs_joined:
            audit_bits.append(f"evidence_refs={_esc(refs_joined)}")
        origin = issue.get("origin")
        if origin:
            audit_bits.append(f"origin={_esc(str(origin))}")
        gate_class = issue.get("gate_class")
        if gate_class:
            audit_bits.append(f"gate={_esc(str(gate_class))}")
        answer_nature = issue.get("answer_nature")
        if answer_nature:
            audit_bits.append(f"nature={_esc(str(answer_nature))}")
        if not finding_id or not source_id or not refs_joined:
            audit_bits.append("provenance=INCOMPLETE")
        audit_html = (
            f"<br><small class='audit'>{' · '.join(audit_bits)}</small>" if audit_bits else ""
        )
        detail_html = f"{pz_html}{audit_html}" or "—"
        rows += (
            f"<tr><td class='sev {_esc(sev)}'>{_esc(sev)}{band_html}</td>"
            f"<td class='{pri_class}'>{pri}</td>"
            f"<td>{conf_display}</td>"
            f"<td>{_esc(issue.get('rule_id', ''))}{loin_html}{norm_html}</td>"
            f"<td>{_esc(issue.get('message', ''))}</td>"
            f"{ev_exp}{ev_obs}"
            f"<td>{_esc(issue.get('element_guid') or '')}</td>"
            f"<td>{_esc(issue.get('target_ref') or '')}</td></tr>\n"
            f"<tr class='detail'><td colspan='9'>{detail_html}</td></tr>\n"
        )
    return rows


def _finding_gates_section(issues: list[dict[str, Any]]) -> str:
    """CORENET-like grouping. Counts are not product accuracy."""

    gates = {"schema": 0, "quality": 0, "regulatory": 0}
    natures = {"deterministic": 0, "probabilistic": 0}
    for issue in issues:
        gate = issue.get("gate_class")
        if gate in gates:
            gates[gate] += 1
        nature = issue.get("answer_nature")
        if nature in natures:
            natures[nature] += 1
    rows = "".join(
        (
            f"<tr><td>{_esc(name)}</td><td>{count}</td></tr>\n"
            for name, count in (*gates.items(), *natures.items())
        )
    )
    return (
        "<section class='cat' id='finding-gates'>"
        "<h2>Finding gates (schema / quality / regulatory)</h2>"
        "<p class='overlay-note'>"
        "Report grouping analog to CORENET X Model Checker stages "
        "(schema, quality, regulatory). Not product accuracy. Not a 90% claim. "
        "Deterministic rows are engine predicates. Probabilistic rows are "
        "advisory origin and never write summary.passed (ADR-001)."
        "</p>"
        "<table><thead><tr><th>Class</th><th>Count</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></section>\n"
    )


def _build_coverage_section(coverage: dict[str, Any]) -> str:
    """WP-R4: coverage map is the first substantive section (before findings)."""
    tz_gaps = coverage.get("tz_gaps") or []
    sources = coverage.get("sources") or []
    if not tz_gaps and not sources:
        return ""

    gap_rows = ""
    for gap in tz_gaps:
        if not isinstance(gap, dict):
            continue
        gap_rows += (
            f"<tr><td>{_esc(str(gap.get('label', '')))}</td>"
            f"<td class='cov-not-checked'><code>{_esc(str(gap.get('status', '')))}</code></td>"
            f"<td>{_esc(str(gap.get('reason', '')))}</td></tr>\n"
        )

    family_keys: list[str] = sorted(
        {
            fam
            for row in sources
            if isinstance(row, dict)
            for fam in (row.get("operator_status") or row.get("families") or {})
        }
    )
    source_rows = ""
    for row in sources:
        if not isinstance(row, dict):
            continue
        sid = _esc(str(row.get("source_id", "")))
        ops = row.get("operator_status") or row.get("families") or {}
        reasons = row.get("reasons") or {}
        cells = ""
        for fam in family_keys:
            op = str(ops.get(fam, "not_checked"))
            reason = reasons.get(fam)
            title = f' title="{_esc(str(reason))}"' if reason else ""
            cells += f"<td class='cov-{op.replace('_', '-')}'{title}><code>{_esc(op)}</code></td>"
        source_rows += f"<tr><td><code>{sid}</code></td>{cells}</tr>\n"

    fam_headers = "".join(f"<th>{_esc(f.replace('-', ' '))}</th>" for f in family_keys)
    tz_block = ""
    if gap_rows:
        tz_block = (
            "<h3>Пробелы матрицы ТЗ (честные not_checked)</h3>"
            "<table class='coverage-tz'><thead><tr><th>Раздел</th><th>Статус</th><th>Причина</th>"
            f"</tr></thead><tbody>{gap_rows}</tbody></table>"
        )

    src_block = ""
    if source_rows:
        src_block = (
            "<h3>По источникам комплекта</h3>"
            "<table class='coverage-src'><thead><tr><th>Источник</th>"
            f"{fam_headers}</tr></thead><tbody>{source_rows}</tbody></table>"
        )

    return (
        "<section class='coverage'><h2>Карта покрытия проверок</h2>"
        "<p class='coverage-note'>«Нарушений не найдено» ≠ «не проверялось». "
        "Не смешивать с итоговым вердиктом.</p>"
        f"{tz_block}{src_block}</section>\n"
    )


def coverage_lines_for_export(coverage: dict[str, Any]) -> list[str]:
    """Plain-text coverage block for PDF export (WP-R4 first page)."""

    lines: list[str] = []
    tz_gaps = coverage.get("tz_gaps") or []
    if tz_gaps:
        lines.append("TZ gaps (honest not_checked):")
        for gap in tz_gaps:
            if not isinstance(gap, dict):
                continue
            lines.append(
                f"  - {gap.get('label', '')}: {gap.get('status', '')} — {gap.get('reason', '')}"
            )
    sources = coverage.get("sources") or []
    if sources:
        lines.append("")
        lines.append("Per-source coverage:")
        for row in sources:
            if not isinstance(row, dict):
                continue
            sid = row.get("source_id", "")
            pres = row.get("presentation_status") or row.get("operator_status") or {}
            if isinstance(pres, dict):
                fam_bits = ", ".join(f"{k}={v}" for k, v in sorted(pres.items()))
                lines.append(f"  {sid}: {fam_bits}")
    if not lines:
        lines.append("(no coverage data)")
    return lines


_ALLOWED_OVERLAY_HREFS = frozenset({"overlay-problem-zone.png"})


def _text_evidence_section(annotations: object) -> str:
    if not isinstance(annotations, list | tuple):
        return ""
    rows = ""
    for ann in annotations:
        if not isinstance(ann, dict):
            continue
        pz = ann.get("problem_zone") if isinstance(ann.get("problem_zone"), dict) else {}
        coords = ""
        if pz:
            coords = (
                f"page={pz.get('page_number')} "
                f"x={pz.get('x')} y={pz.get('y')} "
                f"w={pz.get('width')} h={pz.get('height')}"
            )
        rows += (
            f"<tr><td>{_esc(str(ann.get('sheet_id') or ''))}</td>"
            f"<td>{_esc(str(ann.get('source_id') or ann.get('source') or ''))}</td>"
            f"<td>{_esc(coords)}</td>"
            f"<td>{_esc(str(ann.get('observed_value') or ''))} "
            f"{_esc(str(ann.get('unit') or ''))}</td>"
            f"<td>{_esc(str(ann.get('target_ref') or ''))}</td></tr>\n"
        )
    if not rows:
        return ""
    return (
        "<section class='cat' id='kt2-text-evidence'><h2>Text evidence</h2>"
        "<p class='overlay-note'>PDF text-layer extraction. Not trained CV.</p>"
        "<table><thead><tr><th>Sheet</th><th>Source</th><th>Coordinates</th>"
        "<th>Extracted</th><th>Target</th></tr></thead><tbody>"
        f"{rows}</tbody></table></section>\n"
    )


def _claim_boundary_banner(release: object) -> str:
    if not isinstance(release, dict) or not release:
        return ""
    return (
        '<p class="claim-boundary" id="kt2-claim-boundary">'
        "Fixture demo. Not customer accuracy. Checkpoint NO_GO. Not CV. "
        "Not a CDE import (structural ZIP / file ingest only). "
        "VLM/advisory cannot set PASS."
        "</p>\n"
    )


def _kt2_release_section(release: object) -> str:
    if not isinstance(release, dict) or not release:
        return ""
    rows = ""
    for key in (
        "git_sha",
        "working_tree_dirty",
        "package_id",
        "document_path",
        "document_sha256",
        "page_number",
        "verification_status",
        "checkpoint_verdict",
        "reproducibility_hash",
    ):
        if key in release and release[key] is not None:
            rows += (
                f"<tr><th>{_esc(key)}</th><td><code>{_esc(str(release[key]))}</code></td></tr>\n"
            )
    coords = release.get("coordinates")
    if isinstance(coords, dict):
        coord_text = ", ".join(f"{k}={coords[k]}" for k in coords)
        rows += f"<tr><th>coordinates</th><td><code>{_esc(coord_text)}</code></td></tr>\n"
    if not rows:
        return ""
    return (
        "<section class='cat' id='kt2-release'><h2>Run identity</h2>"
        f"<table><tbody>{rows}</tbody></table></section>\n"
    )


def _capability_rows(capabilities: object) -> str:
    if not isinstance(capabilities, dict):
        return ""
    rows = ""
    for name, payload in sorted(capabilities.items()):
        if isinstance(payload, dict):
            status = payload.get("status", "")
            reason = payload.get("reason") or ""
        else:
            status = payload
            reason = ""
        status_text = getattr(status, "value", status)
        rows += (
            f"<tr><td>{_esc(str(name))}</td>"
            f"<td>{_esc(str(status_text))}</td>"
            f"<td>{_esc(str(reason))}</td></tr>\n"
        )
    if not rows:
        return ""
    return (
        "<section class='cat' id='kt2-capabilities'><h2>Capability honesty</h2>"
        "<table><thead><tr><th>Capability</th><th>Status</th><th>Reason</th>"
        "</tr></thead><tbody>"
        f"{rows}</tbody></table></section>\n"
    )


def _overlay_section(overlay_image_href: str | None) -> str:
    """Sibling PNG only — never a remote or path-escaping href."""
    if overlay_image_href not in _ALLOWED_OVERLAY_HREFS:
        return ""
    href = _esc(overlay_image_href)
    return (
        "<section class='overlay' id='kt2-overlay'>"
        "<h2>Problem-zone overlay</h2>"
        "<p class='overlay-note'>"
        "Fixture demo. Not customer accuracy. Deterministic bbox on rasterized "
        "PDF text-layer sheet. Not CV. Not stamp product. Not a CDE import."
        "</p>"
        f"<figure><img src='{href}' alt='Problem-zone overlay on sheet' />"
        f"<figcaption>{href} — highlighted region, sibling of this HTML</figcaption>"
        "</figure>"
        "</section>\n"
    )


def render_report_html(
    report_id: str,
    data: dict[str, Any],
    *,
    overlay_image_href: str | None = None,
) -> str:
    """Render the serialized public report payload as a standalone HTML page."""
    summary: dict[str, Any] = data["summary"]
    passed = bool(summary.get("passed"))
    status_class = "pass" if passed else "fail"
    status_label = "PASSED" if passed else "FAILED"
    raw_outcome = summary.get("outcome")
    outcome_text = getattr(raw_outcome, "value", raw_outcome) or "—"

    # Group issues by category for expert reviewer workflow
    category_issues: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for issue in data.get("issues", ()):
        cat = issue.get("category", "ifc-validation")
        category_issues[cat].append(issue)

    iso_fields = [
        ("Stage", data.get("stage")),
        ("CDE container", data.get("information_container_id")),
        ("Revision", data.get("revision")),
        ("Doc status", data.get("doc_status")),
    ]
    iso_rows = "".join(
        f"<tr><th>{_esc(label)}</th><td>{_esc(str(value))}</td></tr>"
        for label, value in iso_fields
        if value is not None
    )
    iso_section = ""
    if iso_rows:
        iso_section = (
            "<section class='cat'><h2>ISO 19650 context</h2>"
            "<table><tbody>"
            f"{iso_rows}"
            "</tbody></table></section>\n"
        )

    category_sections = ""
    cat_labels = {
        "ifc-validation": "IFC Model Validation",
        "ids-validation": "IDS Requirement Validation",
        "drawing-validation": "Drawing Annotation Validation",
        "cross-document": "Cross-Document Contradictions",
        "spatial": "Spatial / Clash Coordination",
    }
    for cat, issues in sorted(category_issues.items()):
        # Known categories map to safe static labels; escape the fallback so a
        # non-enum ``category`` (e.g. from a hand-tampered stored report) cannot
        # inject markup into the <h2>. Defense-in-depth: export CSP has no
        # script-src and is served as an attachment.
        label = cat_labels.get(cat)
        label_html = label if label is not None else _esc(str(cat))
        rows = _build_issue_rows(issues)
        category_sections += (
            f"<section class='cat'><h2>{label_html} ({len(issues)})</h2>"
            f"<table><thead><tr><th>Severity</th><th>Priority</th><th>Confidence</th><th>Rule</th><th>Message</th>"
            f"<th>Expected</th><th>Observed</th><th>GUID</th><th>Target</th></tr></thead>"
            f"<tbody>{rows}</tbody></table></section>\n"
        )

    overlay_html = _overlay_section(overlay_image_href)
    coverage_html = _build_coverage_section(data.get("coverage") or {})
    gates_html = _finding_gates_section(list(data.get("issues") or ()))
    text_evidence_html = _text_evidence_section(data.get("drawing_annotations"))
    capabilities_html = _capability_rows(data.get("capabilities"))
    kt2_release = data.get("kt2_release")
    kt2_release_html = _kt2_release_section(kt2_release)
    claim_banner = _claim_boundary_banner(kt2_release)

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Validation Report {_esc(report_id)}</title>
<style>
:root{{--error:#c00;--warning:#b58900;--info:#555;--bg-pass:#d4edda;--bg-fail:#f8d7da}}
body{{font-family:system-ui,sans-serif;margin:2em;color:#222;line-height:1.5}}
h1{{font-size:1.5em;margin-bottom:.3em}}
h2{{font-size:1.1em;margin:1.2em 0 .5em}}
.summary{{margin:1em 0;padding:1em;border-radius:6px;font-size:1.05em}}
.pass{{background:var(--bg-pass);color:#155724}}
.fail{{background:var(--bg-fail);color:#721c24}}
section.cat{{margin-top:1.5em}}
table{{border-collapse:collapse;width:100%;margin-top:.5em;font-size:.95em}}
th,td{{border:1px solid #ccc;padding:.4em .8em;text-align:left;vertical-align:top}}
th{{background:#f5f5f5}}
td.error,td.sev.error{{color:var(--error);font-weight:600}}
td.warning,td.sev.warning{{color:var(--warning);font-weight:600}}
td.info{{color:var(--info)}}
tr.detail td{{border-top:none;padding-top:0;color:#666;font-size:.85em}}
small.pz{{color:#555}}
.meta{{margin-top:2em;font-size:.85em;color:#888}}
td.pri-high{{color:var(--error);font-weight:700}}
td.pri-med{{color:var(--warning);font-weight:600}}
td.pri-low{{color:var(--info)}}
.band{{display:inline-block;padding:0 .45em;border-radius:9px;font-size:.75em;
font-weight:700;vertical-align:middle}}
.band-critical{{background:#c00;color:#fff}}
.band-major{{background:#b58900;color:#fff}}
.band-minor{{background:#5b7fa6;color:#fff}}
.band-negligible{{background:#999;color:#fff}}
.coverage{{margin:1.5em 0}}
.coverage-note{{font-size:.9em;color:#555;margin:.4em 0 1em}}
.coverage-tz,.coverage-src{{font-size:.9em}}
.cov-no-findings{{background:#e8f5e9}}
.cov-findings{{background:#fff3e0}}
.cov-not-checked{{background:#f5f5f5;color:#666}}
.cov-insufficient-data{{background:#fff8e1}}
.cov-expert-required{{background:#e3f2fd}}
.overlay img{{max-width:100%;height:auto;border:1px solid #ccc}}
.overlay-note{{font-size:.9em;color:#555}}
.claim-boundary{{margin:1em 0;padding:.75em 1em;border:1px solid #b58900;
background:#fff8e1;font-size:.95em}}
</style></head><body>
<h1>Validation Report</h1>
{claim_banner}
<div class="summary {status_class}">
<strong>{status_label}</strong> &mdash;
summary.passed={_esc(str(passed).lower())} &middot;
summary.outcome={_esc(str(outcome_text))} &middot;
{summary["issue_count"]} issue(s): {summary["error_count"]} error(s),
{summary["warning_count"]} warning(s) &middot;
{summary["requirement_count"]} requirement(s)
</div>
{overlay_html}{text_evidence_html}{coverage_html}{gates_html}{capabilities_html}{kt2_release_html}{iso_section}{category_sections}
<p class="meta">
Report ID: {_esc(report_id)} &middot;
Project: {_esc(str(data.get("project_name") or "—"))} &middot;
Discipline: {_esc(str(data.get("discipline") or "—"))} &middot;
Created: {_esc(str(data.get("created_at") or ""))}
</p>
</body></html>"""
