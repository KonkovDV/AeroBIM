"""Build a compact, claim-safe customer review pack from a report JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

SCHEMA_VERSION: Final = "1.0.0"
CLAIM_BOUNDARY: Final = (
    "Customer-review shortlist only. Machine verdict is copied unchanged. "
    "Human review does not establish package acceptance, product accuracy, "
    "customer SLA, CDE import, or contractual fitness."
)
TERMINAL: Final = frozenset({"rejected", "waived", "superseded"})
UNVERIFIED: Final = frozenset({"failed", "missing", "not_implemented", "not_verified", "skipped"})
_PATHS: Final = (
    re.compile(r"(?<!\w)[A-Za-z]:[\\/][^\s|;,]+"),
    re.compile(r"(?<![\w:/])/(?:home|Users|data|tmp|var|opt|srv|mnt)/[^\s|;,]+"),
)


def _map(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _rows(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _text(value: object, limit: int = 4_000) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    for pattern in _PATHS:
        result = pattern.sub("<redacted-path>", result)
    return result[:limit] or None


def _number(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
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


def _location(issue: Mapping[str, Any]) -> dict[str, Any]:
    zone, remark = _map(issue.get("problem_zone")), _map(issue.get("remark"))
    bbox = {
        key: number
        for key in ("x", "y", "width", "height")
        if (number := _number(zone.get(key))) is not None
    }
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
    refs = issue.get("evidence_refs")
    safe_refs = (
        sorted({_text(value, 1_000) for value in refs if _text(value, 1_000)})
        if isinstance(refs, Sequence) and not isinstance(refs, str | bytes | bytearray)
        else []
    )
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
        "evidence_refs": safe_refs,
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
    result = {f"finding:{finding_id}"} if finding_id else set()
    if rule_id and target:
        result.add(f"rule-target:{rule_id}|{target}")
    return result


def _rank(row: Mapping[str, Any]) -> tuple[int, int, int, int, int, float, str]:
    review, confidence = _map(row.get("review")), _map(row.get("confidence"))
    value = _number(confidence.get("value"))
    return (
        0 if review.get("status") == "accepted" else 1,
        0 if row.get("origin") == "deterministic" else 1,
        {"error": 0, "warning": 1, "info": 2}.get(str(row.get("severity")), 3),
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


def build_customer_review_pack(
    report_payload: Mapping[str, Any],
    *,
    top_k: int = 20,
    known_findings_payload: Mapping[str, Any] | None = None,
    generated_at: str | None = None,
    source_report_sha256: str | None = None,
) -> dict[str, Any]:
    """Return a deterministic, whitelisted top-K review document."""
    if not 1 <= top_k <= 100:
        raise ValueError("top_k must be between 1 and 100")
    summary = _map(report_payload.get("summary"))
    all_findings = [_project(row) for row in _rows(report_payload.get("issues"))]
    active = [row for row in all_findings if _map(row.get("review")).get("status") not in TERMINAL]
    active.sort(key=_rank)
    baseline = _baseline(known_findings_payload)
    baseline_keys = {key for row in baseline for key in _keys(row)}
    matched: set[str] = set()
    for row in active:
        overlap = _keys(row) & baseline_keys
        matched.update(overlap)
        row["baseline_comparison"] = (
            "known_match"
            if known_findings_payload is not None and overlap
            else "candidate_not_in_baseline"
            if known_findings_payload is not None
            else "not_compared"
        )
    capabilities: dict[str, Any] = {}
    unverified: list[str] = []
    for name, raw in sorted(_map(report_payload.get("capabilities")).items()):
        item = _map(raw)
        status = (_text(item.get("status") if item else raw, 64) or "unknown").lower()
        capabilities[str(name)] = {
            "status": status,
            "reason": _text(item.get("reason"), 2_000) if item else None,
        }
        if status in UNVERIFIED:
            unverified.append(str(name))
    selected = active[:top_k]
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
            "allowed_decisions": [
                "confirmed",
                "false_positive",
                "needs_context",
                "already_known",
            ],
        },
        "counts": {
            "total_findings": len(all_findings),
            "active_candidates": len(active),
            "selected": len(selected),
            "excluded_terminal": len(all_findings) - len(active),
        },
        "known_baseline": {
            "status": "PROVIDED" if known_findings_payload is not None else "NOT_PROVIDED",
            "finding_count": len(baseline),
            "matched_identity_count": len(matched),
            "note": (
                "candidate_not_in_baseline means no deterministic identity key matched; "
                "it is not a claim that the defect is new."
            ),
        },
        "capabilities": capabilities,
        "not_evaluated_or_unverified": unverified,
        "findings": selected,
    }


def _md(value: object, limit: int = 220) -> str:
    return (_text(value, limit) or "—").replace("|", "\\|").replace("\n", " ")


def render_customer_review_markdown(pack: Mapping[str, Any]) -> str:
    """Render a compact human-review surface."""
    scope, machine = _map(pack.get("scope")), _map(pack.get("machine_result"))
    lines = [
        "# AeroBIM — пакет экспертного ревью",
        "",
        ("> Это shortlist для решения эксперта, не акт приёмки и не метрика точности."),
        "",
        f"- Проект: {_md(scope.get('project_name'))}",
        (f"- Машинный результат: `passed={str(bool(machine.get('passed'))).lower()}`"),
        f"- Customer acceptance: `{pack.get('customer_acceptance')}`",
        f"- Accuracy / SLA: `{pack.get('accuracy_claim')}` / `{pack.get('sla_claim')}`",
        "",
        "| # | Severity | Origin | Rule | Суть | Baseline | Решение |",
        "|---:|---|---|---|---|---|---|",
    ]
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
                    _md(row.get("baseline_comparison"), 64),
                    _md(decision.get("status"), 64),
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Решения: `confirmed`, `false_positive`, `needs_context`, `already_known`.",
            "",
            str(pack.get("claim_boundary") or CLAIM_BOUNDARY),
            "",
        ]
    )
    return "\n".join(lines)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-json", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--top-k", default=20, type=int)
    parser.add_argument("--known-findings-json", type=Path)
    args = parser.parse_args(argv)
    try:
        report_bytes = args.report_json.read_bytes()
        report = json.loads(report_bytes.decode())
        known = (
            json.loads(args.known_findings_json.read_text(encoding="utf-8"))
            if args.known_findings_json
            else None
        )
        if not isinstance(report, dict) or (known is not None and not isinstance(known, dict)):
            raise ValueError("inputs must contain JSON objects")
        pack = build_customer_review_pack(
            report,
            top_k=args.top_k,
            known_findings_payload=known,
            source_report_sha256=_sha(report_bytes),
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"customer review pack failed: {exc}", file=sys.stderr)
        return 2
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "customer-review.json": json.dumps(pack, ensure_ascii=False, indent=2) + "\n",
        "customer-review.md": render_customer_review_markdown(pack),
    }
    for name, content in outputs.items():
        (args.output_dir / name).write_text(content, encoding="utf-8", newline="\n")
    manifest = {
        "artifact_type": "aerobim_customer_review_pack_manifest",
        "schema_version": SCHEMA_VERSION,
        "source_report_sha256": pack["source_report_sha256"],
        "customer_acceptance": "NOT_EVALUATED",
        "files": {
            name: {"sha256": _sha(content.encode()), "bytes": len(content.encode())}
            for name, content in outputs.items()
        },
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"ok": True, "selected": len(pack["findings"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
