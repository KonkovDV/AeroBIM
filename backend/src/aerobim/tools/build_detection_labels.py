"""Compile a two-adjudicator CSV worksheet into a detection-precision label set.

This is a thin intake wrapper so that, when a customer corpus arrives, two
engineers fill ``adjudication-template.csv`` independently and this tool
reconciles their verdicts into ``labels.json`` in the exact schema consumed by
``aerobim-evaluate-detection-precision``. It performs **no** fuzzy matching and
bakes **no** accuracy thresholds (thresholds live in the evaluator and gate only
synthetic fixtures in CI).

Verdict semantics (per row, per adjudicator):
    TP / FN -> the finding is a real defect (ground-truth member)
    FP      -> the finding is not a real defect

Reconciliation per finding identity (harness ``exact-v1`` policy:
``case_id`` + ``finding_class`` + [``match_key`` | ``rule_id``+``target_ref``+``element_guid``]):
    all adjudicators say "real"      -> adjudication_status = confirmed
    all adjudicators say "not real"  -> adjudication_status = excluded
    disagreement                     -> adjudication_status = unresolved

``--dataset-status adjudicated`` fails closed unless the two-adjudicator
publishable preconditions hold (>=2 distinct adjudicators, 0 unresolved,
scope_reference, timezone-aware completed_at, recognised method) so nobody can
mint publishable customer evidence by accident.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any

_SCHEMA_VERSION = "1.0.0"
_MAX_ROWS = 200_000
_VERDICTS = {"TP", "FP", "FN"}
_REAL_VERDICTS = {"TP", "FN"}
_DATASET_STATUSES = {"synthetic", "draft", "adjudicated"}
_METHODS = {"consensus", "majority-with-resolution", "dual_independent"}
_REQUIRED_COLUMNS = {
    "case_id",
    "finding_class",
    "rule_id",
    "target_ref",
    "element_guid",
    "match_key",
    "adjudicator_id",
    "verdict",
}


class AdjudicationError(ValueError):
    """Raised when the worksheet is malformed or fails a publishable precondition."""


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _identity(row: dict[str, str | None]) -> tuple[str, str, str, str, str]:
    """Stable finding identity mirroring the evaluator's exact-v1 policy."""
    return (
        row["case_id"] or "",
        row["finding_class"] or "",
        row.get("match_key") or "",
        row.get("rule_id") or "",
        f"{row.get('target_ref') or ''}|{row.get('element_guid') or ''}",
    )


def load_rows(csv_path: Path) -> list[dict[str, str | None]]:
    if not csv_path.is_file():
        raise AdjudicationError(f"Adjudication CSV not found: {csv_path}")
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise AdjudicationError("Adjudication CSV has no header row")
        missing = _REQUIRED_COLUMNS - {name.strip() for name in reader.fieldnames}
        if missing:
            raise AdjudicationError(f"Adjudication CSV missing columns: {sorted(missing)}")
        rows: list[dict[str, str | None]] = []
        for index, raw in enumerate(reader):
            if len(rows) >= _MAX_ROWS:
                raise AdjudicationError(f"Adjudication CSV exceeds {_MAX_ROWS} rows")
            row = {key: _clean(raw.get(key)) for key in reader.fieldnames}
            if not any(row.get(col) for col in ("case_id", "finding_class", "verdict")):
                continue  # skip fully blank lines
            _validate_row(row, index)
            rows.append(row)
    if not rows:
        raise AdjudicationError("Adjudication CSV has no data rows")
    return rows


def _validate_row(row: dict[str, str | None], index: int) -> None:
    where = f"row {index + 2}"  # +2: 1-based + header
    for col in ("case_id", "finding_class", "rule_id", "adjudicator_id", "verdict"):
        if not row.get(col):
            raise AdjudicationError(f"{where}: '{col}' is required")
    verdict = (row["verdict"] or "").upper()
    if verdict not in _VERDICTS:
        raise AdjudicationError(f"{where}: verdict must be one of {sorted(_VERDICTS)}")
    row["verdict"] = verdict
    if not (row.get("target_ref") or row.get("element_guid") or row.get("match_key")):
        raise AdjudicationError(
            f"{where}: a finding needs at least one of target_ref / element_guid / match_key"
        )


def reconcile(
    rows: list[dict[str, str | None]],
) -> tuple[dict[str, list[dict[str, Any]]], int, set[str]]:
    """Return (case_id -> expected_findings, unresolved_count, adjudicator_ids)."""
    by_identity: OrderedDict[tuple[str, str, str, str, str], dict[str, Any]] = OrderedDict()
    adjudicator_ids: set[str] = set()
    for row in rows:
        adjudicator_ids.add(row["adjudicator_id"] or "")
        identity = _identity(row)
        entry = by_identity.setdefault(
            identity,
            {"row": row, "verdicts": {}},
        )
        adj = row["adjudicator_id"] or ""
        prior = entry["verdicts"].get(adj)
        if prior is not None and prior != row["verdict"]:
            raise AdjudicationError(
                f"Adjudicator {adj!r} gave conflicting verdicts for the same finding "
                f"in case {row['case_id']!r}: {prior} vs {row['verdict']}"
            )
        entry["verdicts"][adj] = row["verdict"]

    cases: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
    unresolved = 0
    for entry in by_identity.values():
        row = entry["row"]
        verdicts = set(entry["verdicts"].values())
        real = all(v in _REAL_VERDICTS for v in verdicts)
        not_real = all(v == "FP" for v in verdicts)
        if real:
            status = "confirmed"
        elif not_real:
            status = "excluded"
        else:
            status = "unresolved"
            unresolved += 1
        finding: dict[str, Any] = {
            "finding_class": row["finding_class"],
            "rule_id": row["rule_id"],
            "adjudication_status": status,
        }
        for key in ("target_ref", "element_guid", "match_key"):
            if row.get(key):
                finding[key] = row[key]
        cases.setdefault(row["case_id"] or "", []).append(finding)
    return cases, unresolved, {a for a in adjudicator_ids if a}


def build_labels(
    rows: list[dict[str, str | None]],
    *,
    dataset_id: str,
    dataset_status: str,
    scope_reference: str | None,
    method: str,
    completed_at: str | None,
) -> dict[str, Any]:
    if dataset_status not in _DATASET_STATUSES:
        raise AdjudicationError(f"dataset_status must be one of {sorted(_DATASET_STATUSES)}")
    if method not in _METHODS:
        raise AdjudicationError(f"method must be one of {sorted(_METHODS)}")
    cases, unresolved, adjudicator_ids = reconcile(rows)

    # Draft/synthetic worksheets default completed_at to the (timezone-aware)
    # compile time so the adjudication block is schema-valid; 'adjudicated' must
    # carry a deliberate, explicit completion timestamp (checked below).
    if completed_at is None and dataset_status != "adjudicated":
        completed_at = datetime.now().astimezone().isoformat()

    completed_with_tz = False
    if completed_at:
        try:
            parsed = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
            completed_with_tz = parsed.tzinfo is not None
        except ValueError as exc:
            raise AdjudicationError("completed_at must be ISO 8601") from exc

    if dataset_status == "adjudicated":
        problems: list[str] = []
        if len(adjudicator_ids) < 2:
            problems.append("need >=2 distinct adjudicator_id values")
        if unresolved:
            problems.append(f"{unresolved} unresolved finding(s) remain")
        if not scope_reference:
            problems.append("scope_reference is required")
        if not completed_with_tz:
            problems.append("completed_at (timezone-aware ISO 8601) is required")
        if problems:
            raise AdjudicationError(
                "Refusing to emit 'adjudicated' labels (fail-closed): " + "; ".join(problems)
            )

    payload: dict[str, Any] = {
        "schema_version": _SCHEMA_VERSION,
        "dataset_id": dataset_id,
        "dataset_status": dataset_status,
    }
    if scope_reference:
        payload["scope_reference"] = scope_reference
    adjudication: dict[str, Any] = {"method": method}
    adjudication["completed_at"] = completed_at
    adjudication["adjudicators"] = [
        {"id": adj, "role": "adjudicator"} for adj in sorted(adjudicator_ids)
    ]
    payload["adjudication"] = adjudication
    payload["cases"] = [
        {"case_id": case_id, "expected_findings": findings} for case_id, findings in cases.items()
    ]
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compile a two-adjudicator CSV into detection-precision labels.json"
    )
    parser.add_argument("--adjudication", type=Path, required=True, help="Input worksheet CSV")
    parser.add_argument("--output", type=Path, required=True, help="Output labels.json")
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--dataset-status", choices=sorted(_DATASET_STATUSES), default="draft")
    parser.add_argument("--scope-reference", default=None)
    parser.add_argument("--method", choices=sorted(_METHODS), default="consensus")
    parser.add_argument("--completed-at", default=None, help="Timezone-aware ISO 8601")
    return parser


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rows = load_rows(args.adjudication)
        payload = build_labels(
            rows,
            dataset_id=args.dataset_id,
            dataset_status=args.dataset_status,
            scope_reference=args.scope_reference,
            method=args.method,
            completed_at=args.completed_at,
        )
    except AdjudicationError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    _write_json_atomic(args.output, payload)
    confirmed = sum(
        1
        for case in payload["cases"]
        for finding in case["expected_findings"]
        if finding["adjudication_status"] == "confirmed"
    )
    unresolved = sum(
        1
        for case in payload["cases"]
        for finding in case["expected_findings"]
        if finding["adjudication_status"] == "unresolved"
    )
    print(
        json.dumps(
            {
                "ok": True,
                "output": str(args.output),
                "dataset_status": payload["dataset_status"],
                "cases": len(payload["cases"]),
                "confirmed": confirmed,
                "unresolved": unresolved,
                "adjudicators": len(payload["adjudication"]["adjudicators"]),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
