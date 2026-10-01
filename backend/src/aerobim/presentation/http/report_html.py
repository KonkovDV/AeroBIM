"""HTML rendering for report export (extracted from api.py).

Pure string rendering: takes the already-serialized public report payload and
returns a standalone HTML document. No FastAPI / auth concerns here.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from aerobim.domain.finding_layer import (
    FINDING_LAYER_ORDER,
    HITL_RULE_ID,
    FindingLayer,
    TzSection,
    classify_finding_layer,
    classify_tz_section,
    layer_counts,
    layer_labels,
    layer_notes,
    tz_section_labels,
)
from aerobim.domain.remark_completeness import completeness_table, incomplete_marker
from aerobim.domain.review_projection import review_partition_of


def issue_clause_label(issue: dict[str, Any]) -> str:
    """ИТЗ / СТО / СП stamp. Empty means the field is missing, not invented."""

    remark = issue.get("remark")
    if isinstance(remark, dict):
        cite = str(remark.get("clause_cite") or "").strip()
        if cite:
            return cite
    parts = [
        str(part).strip()
        for part in (issue.get("norm_source"), issue.get("norm_edition"), issue.get("norm_clause"))
        if part and str(part).strip()
    ]
    return " · ".join(parts)


def issue_display_text(issue: dict[str, Any]) -> str:
    """Russian (or overlaid) essence; mirrors frontend ``findingListTitle``."""

    review = issue.get("review")
    if isinstance(review, dict):
        state = str(review.get("state") or "")
        effective = str(review.get("effective_text") or "").strip()
        if state == "edited" and effective:
            return effective
    remark = issue.get("remark")
    if isinstance(remark, dict):
        essence = str(remark.get("essence") or "").strip()
        if essence and not essence.startswith("["):
            return essence
        title = str(remark.get("title") or "").strip()
        if title:
            colon = title.find(": ")
            rest = title[colon + 2 :] if colon >= 0 else title
            for suffix in (" [приоритет", " [priority"):
                cut = rest.find(suffix)
                if cut >= 0:
                    rest = rest[:cut]
            rest = rest.strip()
            if rest and not rest.startswith("["):
                return rest
    return str(issue.get("message") or "")


def issue_location_line(issue: dict[str, Any]) -> str:
    remark = issue.get("remark")
    if isinstance(remark, dict):
        line = str(remark.get("location_line") or "").strip()
        if line:
            return line
    bits: list[str] = []
    storey = issue.get("storey_name")
    if storey:
        bits.append(str(storey))
    axis = issue.get("grid_axis")
    if axis:
        bits.append(str(axis))
    zone = issue.get("problem_zone")
    if isinstance(zone, dict) and zone.get("sheet_id"):
        bits.append(str(zone.get("sheet_id")))
    guid = issue.get("element_guid")
    if guid:
        bits.append(str(guid))
    return "; ".join(bits)


def collapse_hitl_with_multiplicity(
    issues: list[dict[str, Any]],
) -> list[tuple[dict[str, Any], int]]:
    """One HITL row per sheet; multiplicity is shown, rows are not dropped."""

    out: list[tuple[dict[str, Any], int]] = []
    index_by_key: dict[str, int] = {}
    for issue in issues:
        if str(issue.get("rule_id") or "") != HITL_RULE_ID:
            out.append((issue, 1))
            continue
        zone = issue.get("problem_zone")
        sheet = ""
        if isinstance(zone, dict):
            sheet = str(zone.get("sheet_id") or "").strip()
        key = sheet or str(issue.get("message") or "")
        seen = index_by_key.get(key)
        if seen is not None:
            first, count = out[seen]
            out[seen] = (first, count + 1)
            continue
        index_by_key[key] = len(out)
        out.append((issue, 1))
    return out


def _esc(value: str) -> str:
    """HTML-escape user-controlled values for element text and attributes."""
    import html

    return html.escape(str(value), quote=True)


def _esc_count(value: object) -> str:
    """Escape numeric (or tampered) summary counts for HTML insertion (F-07)."""

    return _esc(str(value))


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
            xf = yf = None
            try:
                if pz.get("x") is not None and pz.get("y") is not None:
                    xf = float(pz.get("x"))
                    yf = float(pz.get("y"))
            except (TypeError, ValueError):
                xf = yf = None
            if sheet and xf is not None and yf is not None:
                pz_html = f"<br><small class='pz'>Лист: {sheet} ({xf:.1f}, {yf:.1f})</small>"
            elif sheet:
                pz_html = f"<br><small class='pz'>Лист: {sheet}</small>"
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
        review = issue.get("review")
        if isinstance(review, dict):
            review_bits: list[str] = []
            state = review.get("state")
            if state:
                review_bits.append(f"state={_esc(str(state))}")
            actor = review.get("actor")
            if actor:
                review_bits.append(f"actor={_esc(str(actor))}")
            effective = review.get("effective_text")
            machine = review.get("machine_text")
            if effective:
                review_bits.append(f"effective={_esc(str(effective))}")
            if machine and machine != effective:
                review_bits.append(f"machine={_esc(str(machine))}")
            if review_bits:
                bits = " · ".join(review_bits)
                detail_html = f"{detail_html}<br><small class='review'>{bits}</small>"
        clause = issue_clause_label(issue)
        clause_html = _esc(clause) if clause else "нет пункта"
        rows += (
            f"<tr><td class='sev {_esc(sev)}'>{_esc(sev)}{band_html}</td>"
            f"<td class='{pri_class}'>{pri}</td>"
            f"<td>{conf_display}</td>"
            f"<td>{_esc(issue.get('rule_id', ''))}{loin_html}{norm_html}</td>"
            f"<td class='clause'>{clause_html}</td>"
            f"<td>{_esc(issue.get('message', ''))}</td>"
            f"{ev_exp}{ev_obs}"
            f"<td>{_esc(issue.get('element_guid') or '')}</td>"
            f"<td>{_esc(issue.get('target_ref') or '')}</td></tr>\n"
            f"<tr class='detail'><td colspan='10'>{detail_html}</td></tr>\n"
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
            f"<tr><td>{_esc(name)}</td><td>{_esc_count(count)}</td></tr>\n"
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
        "Fixture demo. Not customer accuracy. Checkpoint GO "
        "(regulatory_measurement_mvp; customer_go false). Not CV. "
        "Not a CDE import (structural ZIP / file ingest only). "
        "VLM/advisory cannot set PASS."
        "</p>\n"
    )


def _executive_brief_section(data: dict[str, Any], *, locale: str) -> str:
    """One-page operational brief. Does not hide skipped or advisory rows."""

    from aerobim.domain.executive_brief import executive_brief

    brief = data.get("executive_brief")
    if not isinstance(brief, dict):
        brief = executive_brief(data)
    ru = locale != "en"
    title = "Краткая выжимка" if ru else "Executive brief"
    mode = (
        "режим: один назначенный эксперт проверяет выданные находки "
        "(не precision/recall, не двойная разметка)"
        if ru
        else "mode: named-expert review of issued findings (not precision/recall)"
    )
    rows = (
        ("pack_findings", "замечаний к комплекту" if ru else "pack findings"),
        ("confirmed", "подтверждено экспертом" if ru else "confirmed"),
        ("edited", "текст эксперта" if ru else "expert text"),
        ("rejected", "отклонено" if ru else "rejected"),
        ("unresolved_review", "ещё без решения эксперта" if ru else "unresolved review"),
        ("advisory_candidates", "кандидаты (не в знаменателе)" if ru else "advisory candidates"),
        ("coverage_notes", "проверки без объектов" if ru else "coverage notes"),
        ("service_records", "служебные записи" if ru else "service records"),
        ("machine_records", "всего машинных записей" if ru else "machine records"),
        ("coverage_not_checked", "ячеек покрытия not_checked" if ru else "coverage not_checked"),
        ("mep_system_clash", "MEP system clash"),
        ("native_dwg", "native DWG"),
        ("calculation_correctness", "calculation correctness"),
        (
            "run_duration_ms",
            "длительность прогона, мс (не SLA)" if ru else "run duration ms (not SLA)",
        ),
    )
    body = ""
    for key, label in rows:
        body += f"<tr><td>{_esc(label)}</td><td>{_esc(str(brief.get(key)))}</td></tr>\n"
    neg = brief.get("negative_capabilities") or ()
    neg_html = ""
    for item in neg:
        if isinstance(item, dict):
            neg_html += (
                f"<tr><td>{_esc(str(item.get('name')))}</td>"
                f"<td>{_esc(str(item.get('status')))}</td></tr>\n"
            )
    if not neg_html:
        neg_html = (
            "<tr><td colspan='2'>"
            + _esc(
                "именованные пробелы: MEP / DWG / calculation в таблице выше"
                if ru
                else "named gaps listed above"
            )
            + "</td></tr>\n"
        )
    disclaimer = str(brief.get("claim_boundary") or "")
    return (
        "<section class='exec-brief' id='executive-brief'>"
        f"<h2>{_esc(title)}</h2>"
        f"<p class='overlay-note'>{_esc(mode)}. hides_negative="
        f"{_esc(str(brief.get('hides_negative')).lower())} · "
        f"is_accuracy={_esc(str(brief.get('is_accuracy')).lower())} · "
        f"is_sla={_esc(str(brief.get('is_sla')).lower())} · "
        f"review_mode={_esc(str(brief.get('review_mode')))}</p>"
        f"<p class='overlay-note'>{_esc(disclaimer)}</p>"
        "<table><thead><tr><th>поле</th><th>значение</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
        "<p class='overlay-note'>"
        + ("Пропуски и NOT_VERIFIED не скрыты." if ru else "SKIPPED and NOT_VERIFIED stay visible.")
        + "</p>"
        "<table><thead><tr><th>capability</th><th>status</th></tr></thead>"
        f"<tbody>{neg_html}</tbody></table></section>\n"
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


def _review_badge(issue: dict[str, Any], *, locale: str) -> str:
    state = review_partition_of(issue)
    if state == "confirmed":
        label = "подтверждено экспертом" if locale != "en" else "confirmed by expert"
        return f" <span class='review-badge confirmed'>{_esc(label)}</span>"
    if state == "edited":
        label = "текст эксперта" if locale != "en" else "expert text"
        return f" <span class='review-badge edited'>{_esc(label)}</span>"
    return ""


def _build_layer_issue_rows(
    issues: list[dict[str, Any]],
    *,
    locale: str,
    collapse_hitl: bool = False,
) -> str:
    rows = ""
    pairs: list[tuple[dict[str, Any], int]]
    if collapse_hitl:
        pairs = collapse_hitl_with_multiplicity(issues)
    else:
        pairs = [(issue, 1) for issue in issues]
    pairs = sorted(pairs, key=lambda pair: pair[0].get("priority", 0), reverse=True)
    for issue, multiplicity in pairs:
        sev = issue.get("severity", "")
        pri = issue.get("priority", 0)
        pri_class = "pri-high" if pri >= 45 else "pri-med" if pri >= 25 else "pri-low"
        band = _triage_band(issue)
        band_html = f" <span class='band band-{band}'>{_esc(band)}</span>" if band else ""
        display = issue_display_text(issue)
        clause = issue_clause_label(issue)
        clause_html = _esc(clause) if clause else ("нет пункта" if locale != "en" else "no clause")
        location = issue_location_line(issue) or ("—" if locale != "en" else "—")
        marker = incomplete_marker(issue, locale=locale)
        marker_html = f" <span class='incomplete'>{_esc(marker)}</span>" if marker else ""
        multi_html = f" <span class='hitl-n'>×{multiplicity}</span>" if multiplicity > 1 else ""
        finding_id = issue.get("finding_id") or ""
        machine = str(issue.get("message") or "")
        review = issue.get("review") if isinstance(issue.get("review"), dict) else {}
        if isinstance(review, dict) and review.get("machine_text"):
            machine_line = str(review.get("machine_text") or "")
        else:
            machine_line = machine
        audit = f"finding_id={_esc(str(finding_id))}" if finding_id else ""
        origin = issue.get("origin")
        if origin:
            audit = (
                f"{audit} · origin={_esc(str(origin))}" if audit else f"origin={_esc(str(origin))}"
            )
        gate = issue.get("gate_class")
        if gate:
            audit = f"{audit} · gate={_esc(str(gate))}" if audit else f"gate={_esc(str(gate))}"
        if isinstance(review, dict):
            actor = review.get("actor")
            if actor:
                audit = (
                    f"{audit} · actor={_esc(str(actor))}" if audit else f"actor={_esc(str(actor))}"
                )
            state = review.get("state")
            if state:
                audit = (
                    f"{audit} · state={_esc(str(state))}" if audit else f"state={_esc(str(state))}"
                )
        rows += (
            f"<tr><td class='sev {_esc(sev)}'>{_esc(sev)}{band_html}</td>"
            f"<td class='{pri_class}'>{pri}</td>"
            f"<td>{_esc(str(issue.get('rule_id', '')))}</td>"
            f"<td class='essence'>{_esc(display)}{_review_badge(issue, locale=locale)}"
            f"{multi_html}{marker_html}</td>"
            f"<td class='clause'>{clause_html}</td>"
            f"<td>{_esc(location)}</td>"
            f"<td>{_esc(str(issue.get('element_guid') or ''))}</td></tr>\n"
            f"<tr class='detail'><td colspan='7'>"
            f"<small class='audit'>{audit}</small>"
            f"<br><small class='machine'>machine={_esc(machine_line)}</small>"
            f"</td></tr>\n"
        )
    return rows


def _issues_table(
    issues: list[dict[str, Any]],
    *,
    locale: str,
    collapse_hitl: bool = False,
) -> str:
    essence = "Суть замечания" if locale != "en" else "Essence"
    clause = "Пункт нормы" if locale != "en" else "Clause"
    location = "Локация" if locale != "en" else "Location"
    severity = "Серьёзность" if locale != "en" else "Severity"
    priority = "Приоритет" if locale != "en" else "Priority"
    rule = "Правило" if locale != "en" else "Rule"
    return (
        "<table><thead><tr>"
        f"<th>{severity}</th><th>{priority}</th><th>{rule}</th>"
        f"<th>{essence}</th><th>{clause}</th><th>{location}</th><th>GUID</th>"
        "</tr></thead>"
        f"<tbody>{_build_layer_issue_rows(issues, locale=locale, collapse_hitl=collapse_hitl)}"
        "</tbody></table>"
    )


def _group_by_tz(issues: list[dict[str, Any]]) -> dict[TzSection, list[dict[str, Any]]]:
    grouped: dict[TzSection, list[dict[str, Any]]] = defaultdict(list)
    for issue in issues:
        grouped[classify_tz_section(issue)].append(issue)
    return grouped


def _build_layer_sections(issues: list[dict[str, Any]], *, locale: str) -> str:
    labels = layer_labels(locale)
    notes = layer_notes(locale)
    tz_labels = tz_section_labels(locale)
    rejected = [item for item in issues if review_partition_of(item) == "rejected"]
    active = [item for item in issues if review_partition_of(item) != "rejected"]
    by_layer: dict[FindingLayer, list[dict[str, Any]]] = {
        layer: [item for item in active if classify_finding_layer(item) == layer]
        for layer in FINDING_LAYER_ORDER
    }
    html = ""
    for layer in FINDING_LAYER_ORDER:
        layer_issues = by_layer[layer]
        heading = labels[layer]
        note = notes[layer]
        if layer in {"pack_finding", "advisory_candidate"}:
            html += (
                f"<section class='layer' id='layer-{layer}'>"
                f"<h2>{_esc(heading)} ({len(layer_issues)})</h2>"
                f"<p class='overlay-note'>{_esc(note)}</p>"
            )
            grouped = _group_by_tz(layer_issues)
            for section in tz_section_labels(locale):
                bucket = grouped.get(section) or []
                if not bucket:
                    continue
                html += (
                    f"<h3>{_esc(tz_labels[section])} ({len(bucket)})</h3>"
                    f"{_issues_table(bucket, locale=locale)}"
                )
            html += "</section>\n"
            continue
        collapse = layer == "service_record"
        html += (
            f"<section class='layer' id='layer-{layer}'>"
            f"<h2>{_esc(heading)} ({len(layer_issues)})</h2>"
            f"<p class='overlay-note'>{_esc(note)}</p>"
            f"{_issues_table(layer_issues, locale=locale, collapse_hitl=collapse)}"
            "</section>\n"
        )
    if rejected:
        rejected_h = "Отклонено экспертом" if locale != "en" else "Rejected by expert"
        html += (
            f"<section class='layer' id='layer-rejected'>"
            f"<h2>{_esc(rejected_h)} ({len(rejected)})</h2>"
            "<p class='overlay-note'>"
            + (
                "Запись сохранена для аудита и не входит в список замечаний."
                if locale != "en"
                else "Kept for audit; not in the pack-finding list."
            )
            + "</p>"
            f"{_issues_table(rejected, locale=locale)}"
            "</section>\n"
        )
    return html


def _passport_section(data: dict[str, Any], *, locale: str) -> str:
    passport = data.get("run_passport")
    if not isinstance(passport, dict):
        return ""
    title = "Паспорт прогона" if locale != "en" else "Run passport"
    disclaimer = str(passport.get("disclaimer") or "")
    rows = ""
    for stage in passport.get("stages") or ():
        if not isinstance(stage, dict):
            continue
        rows += (
            f"<tr><td>{_esc(str(stage.get('name')))}</td>"
            f"<td>{_esc(str(stage.get('duration_ms')))}</td>"
            f"<td>{_esc(str(stage.get('cumulative_ms')))}</td></tr>\n"
        )
    coverage_raw = passport.get("format_coverage")
    coverage = coverage_raw if isinstance(coverage_raw, dict) else {}
    fmt_rows = ""
    for row in coverage.get("rows") or ():
        if not isinstance(row, dict):
            continue
        fmt_rows += (
            f"<tr><td>{_esc(str(row.get('suffix')))}</td>"
            f"<td>{_esc(str(row.get('disposition')))}</td>"
            f"<td>{_esc(str(row.get('reason')))}</td></tr>\n"
        )
    submitted = coverage.get("submitted", "—")
    read = coverage.get("read", "—")
    rejected = coverage.get("rejected", "—")
    return (
        "<section class='passport' id='run-passport'>"
        f"<h2>{_esc(title)}</h2>"
        f"<p class='overlay-note'>{_esc(disclaimer)} is_sla=false</p>"
        "<table><thead><tr><th>stage</th><th>ms</th><th>cumulative</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        f"<p class='overlay-note'>formats: submitted={_esc(str(submitted))} · "
        f"read={_esc(str(read))} · rejected={_esc(str(rejected))}</p>"
        f"<table><thead><tr><th>suffix</th><th>disposition</th><th>reason</th></tr></thead>"
        f"<tbody>{fmt_rows}</tbody></table></section>\n"
    )


def _calculation_export_section(data: dict[str, Any], *, locale: str) -> str:
    section = data.get("calculation_section")
    if not isinstance(section, dict):
        return ""
    title = "Сверка с расчётом" if locale != "en" else "Calculation compare"
    note = (
        "Сверка заявленных значений между документом и моделью; независимый пересчёт вне scope MVP."
        if locale != "en"
        else "Declared-value compare; independent recalculation is out of MVP scope."
    )
    rows = ""
    for row in section.get("rows") or ():
        if not isinstance(row, dict):
            continue
        rows += (
            f"<tr><td>{_esc(str(row.get('id')))}</td>"
            f"<td>{_esc(str(row.get('label')))}</td>"
            f"<td>{_esc(str(row.get('status')))}</td>"
            f"<td>{_esc(str(row.get('note')))}</td></tr>\n"
        )
    return (
        "<section class='calc' id='calculation-compare'>"
        f"<h2>{_esc(title)}</h2>"
        f"<p class='overlay-note'>{_esc(note)}</p>"
        "<table><thead><tr><th>id</th><th>check</th><th>status</th><th>note</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></section>\n"
    )


def _revision_section(data: dict[str, Any], *, locale: str) -> str:
    diff = data.get("revision_diff")
    if not isinstance(diff, dict):
        return ""
    title = "Сравнение с ревизией" if locale != "en" else "Revision compare"
    honesty = (
        "«не воспроизведено» не означает «исправлено»: проверка могла не выполниться повторно."
        if locale != "en"
        else "'no longer reported' does not mean 'fixed'; the check may not have re-run."
    )

    def _lis(key: str) -> str:
        values = diff.get(key) or []
        if not isinstance(values, list):
            return ""
        return "".join(f"<li>{_esc(str(item))}</li>" for item in values)

    newly = "новые" if locale != "en" else "newly_reported"
    still = "ещё есть" if locale != "en" else "still_reported"
    gone = "не воспроизведено" if locale != "en" else "no_longer_reported"
    return (
        "<section class='revision' id='revision-diff'>"
        f"<h2>{_esc(title)}</h2>"
        f"<p class='overlay-note'>{_esc(honesty)}</p>"
        f"<h3>{_esc(newly)}</h3><ul>{_lis('newly_reported')}</ul>"
        f"<h3>{_esc(still)}</h3><ul>{_lis('still_reported')}</ul>"
        f"<h3>{_esc(gone)}</h3><ul>{_lis('no_longer_reported')}</ul>"
        "</section>\n"
    )


def _completeness_section(issues: list[dict[str, Any]], *, locale: str) -> str:
    table = completeness_table(issues)
    title = "Полнота замечания (формат 2.1.5)" if locale != "en" else "Remark completeness (2.1.5)"
    note = (
        "Доля строк слоя «замечания к комплекту» с сутью, пунктом и локацией. Не точность продукта."
        if locale != "en"
        else "Share of pack-finding rows with essence, clause and location. Not product accuracy."
    )
    return (
        "<section class='completeness' id='remark-completeness'>"
        f"<h2>{_esc(title)}</h2>"
        f"<p class='overlay-note'>{_esc(note)} "
        f"claim_level={_esc(str(table['claim_level']))} · is_accuracy=false</p>"
        "<table><thead><tr>"
        f"<th>{'Показатель' if locale != 'en' else 'Metric'}</th>"
        f"<th>{'Значение' if locale != 'en' else 'Value'}</th>"
        "</tr></thead><tbody>"
        f"<tr><td>pack_finding</td><td>{_esc_count(table['pack_finding_count'])}</td></tr>"
        f"<tr><td>full_triad</td><td>{_esc_count(table['full_triad_count'])}</td></tr>"
        f"<tr><td>share_full_triad</td><td>{_esc(str(table['share_full_triad']))}</td></tr>"
        "</tbody></table></section>\n"
    )


def _layer_header(issues: list[dict[str, Any]], *, locale: str) -> str:
    counts = layer_counts(issues)
    rejected = sum(1 for item in issues if review_partition_of(item) == "rejected")
    confirmed = sum(
        1
        for item in issues
        if classify_finding_layer(item) == "pack_finding"
        and review_partition_of(item) == "confirmed"
    )
    pack_shown = sum(
        1
        for item in issues
        if classify_finding_layer(item) == "pack_finding"
        and review_partition_of(item) != "rejected"
    )
    if locale == "en":
        return (
            "<p class='layer-break' id='layer-breakdown'>"
            f"pack findings: {_esc_count(pack_shown)} · "
            f"confirmed: {_esc_count(confirmed)} · "
            f"rejected: {_esc_count(rejected)} · "
            f"coverage notes: {_esc_count(counts['coverage_note'])} · "
            f"service records: {_esc_count(counts['service_record'])} · "
            f"candidates: {_esc_count(counts['advisory_candidate'])} · "
            f"machine records: {_esc_count(len(issues))}"
            "</p>\n"
        )
    return (
        "<p class='layer-break' id='layer-breakdown'>"
        f"замечаний к комплекту: {_esc_count(pack_shown)} · "
        f"подтверждено экспертом: {_esc_count(confirmed)} · "
        f"отклонено: {_esc_count(rejected)} · "
        f"проверок без объектов: {_esc_count(counts['coverage_note'])} · "
        f"служебных записей: {_esc_count(counts['service_record'])} · "
        f"кандидатов: {_esc_count(counts['advisory_candidate'])} · "
        f"всего машинных записей: {_esc_count(len(issues))}"
        "</p>\n"
    )


def render_report_html(
    report_id: str,
    data: dict[str, Any],
    *,
    overlay_image_href: str | None = None,
    locale: str = "ru",
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
            f"<table><thead><tr><th>Severity</th><th>Priority</th><th>Confidence</th><th>Rule</th>"
            f"<th>ИТЗ / СТО / СП</th><th>Message</th>"
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
    issue_rows = [item for item in data.get("issues") or () if isinstance(item, dict)]
    normalized_locale = "en" if str(locale).strip().lower().startswith("en") else "ru"
    html_lang = "en" if normalized_locale == "en" else "ru"
    page_title = "Validation Report"
    heading = "Отчёт проверки" if normalized_locale != "en" else "Validation Report"
    appendix_title = (
        "Приложение: полный машинный лог"
        if normalized_locale != "en"
        else "Appendix: full machine log"
    )
    layer_html = _build_layer_sections(issue_rows, locale=normalized_locale)
    completeness_html = _completeness_section(issue_rows, locale=normalized_locale)
    passport_html = _passport_section(data, locale=normalized_locale)
    calculation_html = _calculation_export_section(data, locale=normalized_locale)
    revision_html = _revision_section(data, locale=normalized_locale)
    breakdown_html = _layer_header(issue_rows, locale=normalized_locale)
    brief_html = _executive_brief_section(data, locale=normalized_locale)
    appendix_html = (
        f"<section class='appendix' id='machine-log'><h2>{_esc(appendix_title)}</h2>"
        f"{category_sections}</section>\n"
        if category_sections
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="{html_lang}"><head><meta charset="utf-8">
<title>{page_title} {_esc(report_id)}</title>
<style>
:root{{--error:#c00;--warning:#b58900;--info:#555;--bg-pass:#d4edda;--bg-fail:#f8d7da}}
body{{font-family:system-ui,sans-serif;margin:2em;color:#222;line-height:1.5}}
h1{{font-size:1.5em;margin-bottom:.3em}}
h2{{font-size:1.1em;margin:1.2em 0 .5em}}
.summary{{margin:1em 0;padding:1em;border-radius:6px;font-size:1.05em}}
.pass{{background:var(--bg-pass);color:#155724}}
.fail{{background:var(--bg-fail);color:#721c24}}
section.cat,section.layer,section.appendix{{margin-top:1.5em}}
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
.exec-brief{{margin:1em 0;padding:.75em 1em;border:1px solid #ccc;background:#fafafa}}
.layer-break{{margin:.75em 0;font-size:.95em}}
.incomplete{{display:inline-block;margin-left:.4em;color:#721c24;font-size:.8em}}
.review-badge{{display:inline-block;margin-left:.4em;padding:0 .4em;border-radius:8px;
font-size:.75em;background:#e8f5e9}}
.review-badge.edited{{background:#e3f2fd}}
.hitl-n{{font-weight:700}}
</style></head><body>
<h1>{heading}</h1>
{claim_banner}
{brief_html}
<div class="summary {status_class}">
<strong>{status_label}</strong> &mdash;
summary.passed={_esc(str(passed).lower())} &middot;
summary.outcome={_esc(str(outcome_text))} &middot;
{_esc_count(summary["issue_count"])} issue(s): {_esc_count(summary["error_count"])} error(s),
{_esc_count(summary["warning_count"])} warning(s) &middot;
{_esc_count(summary["requirement_count"])} requirement(s)
</div>
{breakdown_html}
{overlay_html}{text_evidence_html}{coverage_html}{passport_html}{calculation_html}{revision_html}{completeness_html}{layer_html}{gates_html}{capabilities_html}{kt2_release_html}{iso_section}{appendix_html}
<p class="meta">
Report ID: {_esc(report_id)} &middot;
Project: {_esc(str(data.get("project_name") or "—"))} &middot;
Discipline: {_esc(str(data.get("discipline") or "—"))} &middot;
Created: {_esc(str(data.get("created_at") or ""))}
</p>
</body></html>"""
