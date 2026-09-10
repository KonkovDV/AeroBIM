"""Build a compact, claim-safe customer review pack from a report JSON."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

SCHEMA_VERSION: Final = "1.1.0"
CLAIM_BOUNDARY: Final = (
    "Customer-review shortlist only. Machine verdict is copied unchanged. "
    "Human review does not establish package acceptance, product accuracy, "
    "customer SLA, CDE import, or contractual fitness."
)
BASELINE_NOTE: Final = (
    "candidate_not_in_baseline means no deterministic identity key matched; "
    "it is not a claim that the defect is new. coverage_ratio is identity-key "
    "overlap with the supplied baseline, never recall, precision, or accuracy."
)
TERMINAL: Final = frozenset({"rejected", "waived", "superseded"})
UNVERIFIED: Final = frozenset({"failed", "missing", "not_implemented", "not_verified", "skipped"})
DECISIONS: Final = ("confirmed", "false_positive", "needs_context", "already_known")
COMPLETENESS_RANK: Final = {"full": 0, "partial": 1, "statement_only": 2, "insufficient": 3}
FORM_COLUMNS: Final = (
    "#",
    "finding_id",
    "rule_id",
    "severity",
    "origin",
    "statement",
    "source_a",
    "source_b",
    "observed",
    "expected",
    "unit",
    "norm_clause",
    "locator",
    "evidence_completeness",
    "confidence",
    "machine_status",
    "baseline",
    "similar_count",
    "decision",
    "comment",
    "reviewer",
    "decided_at",
)
_PATHS: Final = (
    re.compile(r"(?<!\w)[A-Za-z]:[\\/][^\s|;,]+"),
    re.compile(r"(?<![\w:/])/(?:home|Users|data|tmp|var|opt|srv|mnt)/[^\s|;,]+"),
)


def _map(value: object) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): item for key, item in value.items()}


def _rows(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        return []
    return [_map(row) for row in value if isinstance(row, Mapping)]


def _text(value: object, limit: int = 4_000) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    for pattern in _PATHS:
        result = pattern.sub("<redacted-path>", result)
    return result[:limit] or None


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if result == result and abs(result) != float("inf") else None


def _integer(value: object) -> int:
    try:
        return 0 if isinstance(value, bool) else int(str(value))
    except (TypeError, ValueError):
        return 0


def _safe_texts(value: object, limit: int = 1_000) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        return []
    texts: set[str] = set()
    for item in value:
        text = _text(item, limit)
        if text is not None:
            texts.add(text)
    return sorted(texts)


def _location(issue: Mapping[str, Any]) -> dict[str, Any]:
    zone, remark = _map(issue.get("problem_zone")), _map(issue.get("remark"))
    bbox: dict[str, float] = {}
    for key in ("x", "y", "width", "height"):
        number = _number(zone.get(key))
        if number is not None:
            bbox[key] = number
    return {
        "source_id": _text(issue.get("source_id"), 1_000),
        "sheet_id": _text(zone.get("sheet_id") or remark.get("sheet_id"), 1_000),
        "page_number": _integer(zone.get("page_number")) or None,
        "bbox": bbox or None,
        "element_guid": _text(issue.get("element_guid") or zone.get("element_guid"), 256),
        "target_ref": _text(issue.get("target_ref"), 1_000),
        "storey_name": _text(issue.get("storey_name") or remark.get("storey_name"), 512),
        "grid_axis": _text(issue.get("grid_axis") or remark.get("grid_axis"), 256),
    }


def _project(issue: Mapping[str, Any]) -> dict[str, Any]:
    review, remark = _map(issue.get("review")), _map(issue.get("remark"))
    state = (_text(review.get("state"), 64) or "pending").lower()
    machine = _text(remark.get("body") or issue.get("message"))
    return {
        "finding_id": _text(issue.get("finding_id"), 256),
        "rule_id": _text(issue.get("rule_id"), 512),
        "category": _text(issue.get("category"), 128),
        "severity": (_text(issue.get("severity"), 32) or "info").lower(),
        "priority": _integer(issue.get("priority")),
        "origin": (_text(issue.get("origin"), 32) or "unknown").lower(),
        "message": _text(issue.get("message")),
        "machine_text": machine,
        "effective_text": _text(review.get("effective_text")) or machine,
        "expected": _text(issue.get("expected_value"), 2_000),
        "observed": _text(issue.get("observed_value"), 2_000),
        "unit": _text(issue.get("unit"), 64),
        "location": _location(issue),
        "norm": {
            "source": _text(issue.get("norm_source"), 512),
            "edition": _text(issue.get("norm_edition"), 256),
            "clause": _text(issue.get("norm_clause"), 256),
            "approval_status": _text(issue.get("approval_status"), 64),
            "approval_ref": _text(issue.get("approval_ref"), 1_000),
        },
        "evidence_refs": _safe_texts(issue.get("evidence_refs")),
        "confidence": {
            "value": _number(issue.get("confidence")),
            "calibrated": issue.get("confidence_calibrated") is True,
            "note": "Extraction confidence only; not probability of a true defect.",
        },
        "review": {
            "status": state,
            "actor": _text(review.get("actor"), 256),
            "event_id": _text(review.get("event_id"), 256),
        },
        "customer_decision": {"status": state, "comment": None},
    }


def _keys(row: Mapping[str, Any]) -> set[str]:
    location = _map(row.get("location"))
    finding_id = _text(row.get("finding_id"), 256)
    rule_id = _text(row.get("rule_id"), 512)
    target = _text(
        row.get("target_ref")
        or row.get("element_guid")
        or location.get("target_ref")
        or location.get("element_guid"),
        1_000,
    )
    keys: set[str] = set()
    if finding_id:
        keys.add(f"finding:{finding_id}")
    if rule_id and target:
        keys.add(f"rule-target:{rule_id}|{target}")
    return keys


def _locator(row: Mapping[str, Any]) -> str | None:
    location = _map(row.get("location"))
    page = _integer(location.get("page_number")) or None
    candidates = (
        _text(location.get("element_guid"), 256),
        _text(location.get("target_ref"), 512),
        _text(location.get("sheet_id"), 512),
        f"p.{page}" if page else None,
        _text(location.get("storey_name"), 256),
        _text(location.get("grid_axis"), 128),
        _text(location.get("source_id"), 512),
    )
    found = [item for item in candidates if item]
    return " / ".join(found[:4]) or None


def _completeness(row: Mapping[str, Any]) -> str:
    sides = sum(1 for key in ("observed", "expected") if row.get(key) is not None)
    if _locator(row) is None or not row.get("effective_text"):
        return "insufficient"
    if sides == 2:
        return "full"
    return "partial" if sides == 1 else "statement_only"


def _gaps(row: Mapping[str, Any]) -> list[str]:
    gaps: list[str] = []
    if not row.get("effective_text"):
        gaps.append("no_statement")
    if _locator(row) is None:
        gaps.append("no_locator")
    if row.get("observed") is None:
        gaps.append("no_observed_value")
    if row.get("expected") is None:
        gaps.append("no_expected_value")
    return gaps


def _family(row: Mapping[str, Any]) -> str:
    location = _map(row.get("location"))
    reference = _text(location.get("target_ref") or location.get("element_guid"), 512) or ""
    entity = reference.split(":", 1)[0] if ":" in reference else ""
    return "|".join(
        (
            str(row.get("rule_id") or ""),
            str(row.get("category") or ""),
            str(row.get("severity") or ""),
            entity,
        )
    )


def _rank(row: Mapping[str, Any]) -> tuple[int, int, int, int, int, int, float, str]:
    review, confidence = _map(row.get("review")), _map(row.get("confidence"))
    value = _number(confidence.get("value"))
    return (
        0 if review.get("status") == "accepted" else 1,
        0 if row.get("origin") == "deterministic" else 1,
        {"error": 0, "warning": 1, "info": 2}.get(str(row.get("severity")), 3),
        COMPLETENESS_RANK.get(str(row.get("evidence_completeness")), 3),
        -_integer(row.get("priority")),
        0 if confidence.get("calibrated") is True else 1,
        -(value if value is not None else -1.0),
        str(row.get("finding_id") or row.get("rule_id") or ""),
    )


def _baseline(payload: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    if payload is None:
        return []
    direct = _rows(payload.get("findings"))
    return direct or [
        finding for case in _rows(payload.get("cases")) for finding in _rows(case.get("findings"))
    ]


def _coverage(
    baseline: Sequence[Mapping[str, Any]],
    candidates: Sequence[Mapping[str, Any]],
    *,
    provided: bool,
) -> dict[str, Any]:
    candidate_keys = {key for row in candidates for key in _keys(row)}
    matched = sum(1 for row in baseline if _keys(row) & candidate_keys)
    total = len(baseline)
    return {
        "status": "PROVIDED" if provided else "NOT_PROVIDED",
        "finding_count": total,
        "matched_identity_count": matched,
        "matched_baseline_count": matched,
        "unmatched_baseline_count": total - matched,
        "coverage_ratio": round(matched / total, 3) if total else None,
        "coverage_scope": "identity_key_match_only",
        "note": BASELINE_NOTE,
    }


def _capabilities(report_payload: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    declared = _map(report_payload.get("capabilities"))
    capabilities: dict[str, Any] = {}
    unverified: list[str] = []
    for name in sorted(declared):
        raw = declared.get(name)
        item = _map(raw)
        status = (_text(item.get("status") if item else raw, 64) or "unknown").lower()
        capabilities[name] = {
            "status": status,
            "reason": _text(item.get("reason"), 2_000) if item else None,
        }
        if status in UNVERIFIED:
            unverified.append(name)
    return capabilities, unverified


def _tally(rows: Sequence[Mapping[str, Any]], key: str, limit: int = 10) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        name = str(row.get(key) or "unmapped")
        counts[name] = counts.get(name, 0) + 1
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return dict(ordered[:limit])


def build_customer_review_pack(
    report_payload: Mapping[str, Any],
    *,
    top_k: int = 20,
    known_findings_payload: Mapping[str, Any] | None = None,
    generated_at: str | None = None,
    source_report_sha256: str | None = None,
    include_needs_data: bool = False,
    keep_duplicates: bool = False,
    strict_evidence: bool = False,
) -> dict[str, Any]:
    """Return a deterministic, whitelisted top-K review document with a triage funnel."""
    if not 1 <= top_k <= 100:
        raise ValueError("top_k must be between 1 and 100")
    summary = _map(report_payload.get("summary"))
    all_findings = [_project(row) for row in _rows(report_payload.get("issues"))]
    active = [row for row in all_findings if _map(row.get("review")).get("status") not in TERMINAL]
    baseline = _baseline(known_findings_payload)
    baseline_keys = {key for row in baseline for key in _keys(row)}
    for row in active:
        row["locator"] = _locator(row)
        row["evidence_completeness"] = _completeness(row)
        row["data_gaps"] = _gaps(row)
        row["review_class"] = (
            "needs_data" if row["evidence_completeness"] == "insufficient" else "reviewable"
        )
        overlap = _keys(row) & baseline_keys
        row["baseline_comparison"] = (
            "known_match"
            if known_findings_payload is not None and overlap
            else "candidate_not_in_baseline"
            if known_findings_payload is not None
            else "not_compared"
        )
    active.sort(key=_rank)
    needs_data = [row for row in active if row["review_class"] == "needs_data"]
    eligible = [row for row in active if include_needs_data or row["review_class"] == "reviewable"]
    pool = [
        row
        for row in eligible
        if not strict_evidence or row["evidence_completeness"] == "full"
    ]
    families: dict[str, dict[str, Any]] = {}
    shortlist: list[dict[str, Any]] = []
    collapsed = 0
    for row in pool:
        family = _family(row)
        representative = families.get(family)
        if representative is not None and not keep_duplicates:
            representative["similar_count"] = _integer(representative.get("similar_count")) + 1
            collapsed += 1
            continue
        row["similar_count"] = 1
        families[family] = row
        shortlist.append(row)
    selected = shortlist[:top_k]
    capabilities, unverified = _capabilities(report_payload)
    return {
        "artifact_type": "aerobim_customer_review_pack",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at or datetime.now(tz=UTC).isoformat(),
        "source_report_id": _text(report_payload.get("report_id"), 256),
        "source_report_sha256": source_report_sha256,
        "scope": {
            key: _text(report_payload.get(key), 512)
            for key in ("project_name", "discipline", "stage", "revision", "doc_status")
        },
        "machine_result": {
            "passed": bool(summary.get("passed")),
            "outcome": _text(summary.get("outcome"), 64),
            "authoritative": summary.get("authoritative") is not False,
        },
        "customer_acceptance": "NOT_EVALUATED",
        "accuracy_claim": "NOT_ESTABLISHED",
        "sla_claim": "NOT_ESTABLISHED",
        "claim_boundary": CLAIM_BOUNDARY,
        "review_protocol": {
            "phase": "single_customer_expert_top_k",
            "allowed_decisions": list(DECISIONS),
        },
        "triage": {
            "top_k": top_k,
            "strict_evidence": strict_evidence,
            "duplicates_collapsed": not keep_duplicates,
            "needs_data_included": include_needs_data,
        },
        "counts": {
            "total_findings": len(all_findings),
            "active_candidates": len(active),
            "selected": len(selected),
            "excluded_terminal": len(all_findings) - len(active),
            "deferred_needs_data": len(active) - len(eligible),
            "excluded_incomplete_evidence": len(eligible) - len(pool),
            "duplicates_collapsed": collapsed,
        },
        "funnel": [
            {
                "stage": "machine_findings",
                "count": len(all_findings),
                "reason": "as reported by the run",
            },
            {
                "stage": "terminal_excluded",
                "count": len(all_findings) - len(active),
                "reason": "rejected, waived or superseded in review",
            },
            {
                "stage": "needs_data_deferred",
                "count": len(active) - len(eligible),
                "reason": "no statement or no locator; moved to the data-gap list",
            },
            {
                "stage": "incomplete_evidence_excluded",
                "count": len(eligible) - len(pool),
                "reason": "strict mode keeps only observed and expected value pairs",
            },
            {
                "stage": "duplicates_collapsed",
                "count": collapsed,
                "reason": "same rule, category, severity and element type",
            },
            {
                "stage": "shortlisted",
                "count": len(selected),
                "reason": f"top-{top_k} after ranking",
            },
        ],
        "evidence_completeness_counts": _tally(active, "evidence_completeness", limit=8),
        "needs_data": {
            "count": len(needs_data),
            "by_rule": _tally(needs_data, "rule_id"),
            "note": (
                "Missing statement or locator is an export or input gap, not a confirmed "
                "design defect. Hand this list to the model authors, not to the reviewer."
            ),
        },
        "known_baseline": _coverage(
            baseline,
            active,
            provided=known_findings_payload is not None,
        ),
        "capabilities": capabilities,
        "not_evaluated_or_unverified": unverified,
        "findings": selected,
    }


def _md(value: object, limit: int = 220) -> str:
    return (_text(value, limit) or "—").replace("|", "\\|").replace("\n", " ")


def _cell(value: object, limit: int = 400) -> str:
    return (_text(value, limit) or "").replace("\r", " ").replace("\n", " ")


def render_customer_review_markdown(pack: Mapping[str, Any]) -> str:
    """Render a compact decision-first human-review surface."""
    scope, machine = _map(pack.get("scope")), _map(pack.get("machine_result"))
    counts, baseline = _map(pack.get("counts")), _map(pack.get("known_baseline"))
    coverage = baseline.get("coverage_ratio")
    covered = f"{baseline.get('matched_baseline_count')} из {baseline.get('finding_count')}"
    if coverage is not None:
        covered = f"{covered} (доля {coverage})"
    lines = [
        "# AeroBIM — пакет экспертного ревью",
        "",
        "> Это shortlist для решения эксперта, не акт приёмки и не метрика точности.",
        "",
        f"- Проект: {_md(scope.get('project_name'))}",
        f"- Раздел / стадия / ревизия: {_md(scope.get('discipline'), 64)}"
        f" / {_md(scope.get('stage'), 64)} / {_md(scope.get('revision'), 64)}",
        f"- Машинный результат: `passed={str(bool(machine.get('passed'))).lower()}`",
        f"- Customer acceptance: `{pack.get('customer_acceptance')}`",
        f"- Accuracy / SLA: `{pack.get('accuracy_claim')}` / `{pack.get('sla_claim')}`",
        f"- На ревью: {_integer(counts.get('selected'))}"
        f" из {_integer(counts.get('total_findings'))} машинных находок",
        f"- Совпало с известными замечаниями: {covered}",
        "",
        "## Как получен shortlist",
        "",
        "| Шаг | Количество | Причина |",
        "|---|---:|---|",
    ]
    for stage in _rows(pack.get("funnel")):
        lines.append(
            f"| {_md(stage.get('stage'), 64)} | {_integer(stage.get('count'))}"
            f" | {_md(stage.get('reason'), 140)} |"
        )
    unverified = [str(name) for name in _safe_texts(pack.get("not_evaluated_or_unverified"), 128)]
    lines.extend(
        [
            "",
            "## Что не проверено",
            "",
            "- " + (", ".join(unverified) if unverified else "нет отдельных ограничений в отчёте"),
            "- Пропуски данных вынесены отдельно: "
            f"{_integer(_map(pack.get('needs_data')).get('count'))} находок",
            "",
            "## Находки на решение",
            "",
            "| # | Severity | Origin | Rule | Суть | Наблюдаемое | Ожидаемое | Локатор"
            " | Полнота | Baseline | Решение |",
            "|---:|---|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for index, row in enumerate(_rows(pack.get("findings")), start=1):
        decision = _map(row.get("customer_decision"))
        lines.append(
            "| "
            + " | ".join(
                (
                    str(index),
                    _md(row.get("severity"), 32),
                    _md(row.get("origin"), 32),
                    _md(row.get("rule_id"), 100),
                    _md(row.get("effective_text") or row.get("message")),
                    _md(row.get("observed"), 80),
                    _md(row.get("expected"), 80),
                    _md(row.get("locator"), 120),
                    _md(row.get("evidence_completeness"), 32),
                    _md(row.get("baseline_comparison"), 64),
                    _md(decision.get("status"), 64),
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Решения: " + ", ".join(f"`{name}`" for name in DECISIONS) + ".",
            "",
            str(pack.get("claim_boundary") or CLAIM_BOUNDARY),
            "",
        ]
    )
    return "\n".join(lines)


def render_customer_review_form(pack: Mapping[str, Any]) -> str:
    """Render one pre-filled decision row per finding for a single reviewer."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(FORM_COLUMNS)
    for index, row in enumerate(_rows(pack.get("findings")), start=1):
        sources = _safe_texts(row.get("evidence_refs"))
        norm, confidence = _map(row.get("norm")), _map(row.get("confidence"))
        writer.writerow(
            [
                index,
                _cell(row.get("finding_id"), 256),
                _cell(row.get("rule_id"), 256),
                _cell(row.get("severity"), 32),
                _cell(row.get("origin"), 32),
                _cell(row.get("effective_text") or row.get("message")),
                _cell(sources[0] if sources else row.get("locator")),
                _cell(sources[1] if len(sources) > 1 else None),
                _cell(row.get("observed"), 200),
                _cell(row.get("expected"), 200),
                _cell(row.get("unit"), 64),
                _cell(norm.get("clause"), 200),
                _cell(row.get("locator"), 200),
                _cell(row.get("evidence_completeness"), 32),
                _cell(confidence.get("value"), 32),
                _cell(_map(row.get("review")).get("status"), 32),
                _cell(row.get("baseline_comparison"), 64),
                _integer(row.get("similar_count")),
                "",
                "",
                "",
                "",
            ]
        )
    return buffer.getvalue()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return {str(key): value for key, value in payload.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-json", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--top-k", default=20, type=int)
    parser.add_argument("--known-findings-json", type=Path)
    parser.add_argument("--strict-evidence", action="store_true")
    parser.add_argument("--keep-duplicates", action="store_true")
    parser.add_argument("--include-needs-data", action="store_true")
    args = parser.parse_args(argv)
    report_path: Path = args.report_json
    output_dir: Path = args.output_dir
    known_path: Path | None = args.known_findings_json
    top_k: int = int(args.top_k)
    try:
        report = _load_object(report_path)
        known = _load_object(known_path) if known_path is not None else None
        pack = build_customer_review_pack(
            report,
            top_k=top_k,
            known_findings_payload=known,
            source_report_sha256=_sha(report_path.read_bytes()),
            include_needs_data=bool(args.include_needs_data),
            keep_duplicates=bool(args.keep_duplicates),
            strict_evidence=bool(args.strict_evidence),
        )
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"customer review pack failed: {exc}", file=sys.stderr)
        return 2
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, tuple[str, str]] = {
        "customer-review.json": (json.dumps(pack, ensure_ascii=False, indent=2) + "\n", "utf-8"),
        "customer-review.md": (render_customer_review_markdown(pack), "utf-8"),
        "customer-review-form.csv": (render_customer_review_form(pack), "utf-8-sig"),
    }
    for name, (content, encoding) in outputs.items():
        (output_dir / name).write_text(content, encoding=encoding, newline="")
    manifest = {
        "artifact_type": "aerobim_customer_review_pack_manifest",
        "schema_version": SCHEMA_VERSION,
        "source_report_sha256": pack["source_report_sha256"],
        "customer_acceptance": "NOT_EVALUATED",
        "files": {
            name: {
                "sha256": _sha(content.encode(encoding)),
                "bytes": len(content.encode(encoding)),
            }
            for name, (content, encoding) in outputs.items()
        },
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="",
    )
    counts = _map(pack.get("counts"))
    print(
        json.dumps(
            {
                "ok": True,
                "selected": _integer(counts.get("selected")),
                "deferred_needs_data": _integer(counts.get("deferred_needs_data")),
                "duplicates_collapsed": _integer(counts.get("duplicates_collapsed")),
                "known_coverage_ratio": _map(pack.get("known_baseline")).get("coverage_ratio"),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
