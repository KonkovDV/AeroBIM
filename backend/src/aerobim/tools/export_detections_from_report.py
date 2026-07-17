"""Export frozen detection-run JSON from a ValidationReport (or report dict).

Customer RT-001 path: assemble detections for ``aerobim-evaluate-detection-precision``
without hand-editing. Does **not** make PrecisionClaim publishable.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def findings_from_report_payload(
    payload: dict[str, Any],
    *,
    case_id: str,
    discipline: str | None = None,
) -> list[dict[str, str]]:
    """Map report issues to detection finding records."""

    findings: list[dict[str, str]] = []
    for issue in payload.get("issues") or ():
        if not isinstance(issue, dict):
            continue
        rule_id = str(issue.get("rule_id") or "").strip()
        if not rule_id:
            continue
        category = str(issue.get("category") or "ifc_validation").strip().lower()
        finding_class = _finding_class(category, rule_id)
        record: dict[str, str] = {
            "finding_class": finding_class,
            "rule_id": rule_id,
        }
        target_ref = issue.get("target_ref")
        element_guid = issue.get("element_guid")
        if isinstance(target_ref, str) and target_ref.strip():
            record["target_ref"] = target_ref.strip()
        elif isinstance(element_guid, str) and element_guid.strip():
            record["element_guid"] = element_guid.strip()
        else:
            # Stable synthetic match when report lacks geometry refs
            record["match_key"] = f"report:{rule_id}:{issue.get('finding_id') or ''}"
        if discipline:
            record["discipline"] = discipline
        findings.append(record)
    return findings


def build_detections_document(
    *,
    run_id: str,
    case_id: str,
    report_payload: dict[str, Any],
    discipline: str | None = None,
) -> dict[str, Any]:
    case: dict[str, Any] = {
        "case_id": case_id,
        "findings": findings_from_report_payload(
            report_payload, case_id=case_id, discipline=discipline
        ),
    }
    if discipline:
        case["discipline"] = discipline
    return {
        "schema_version": "1.0.0",
        "run_id": run_id,
        "cases": [case],
        "claim_boundary": (
            "Harness export only — not product accuracy; RT-001 remains open "
            "until customer corpus + adjudication"
        ),
    }


def _finding_class(category: str, rule_id: str) -> str:
    if category in {"spatial", "clash"} or rule_id.upper().startswith("SPATIAL"):
        return "clash"
    if category in {"cross_document", "cross-document"}:
        return "cross-document"
    return category.replace("_", "-") or "ifc-validation"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report-json",
        type=Path,
        required=True,
        help="Path to ValidationReport JSON (public API shape with issues[])",
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--discipline", default=None)
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output detections JSON path",
    )
    args = parser.parse_args(argv)
    payload = json.loads(args.report_json.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        print("report JSON must be an object", file=sys.stderr)
        return 2
    document = build_detections_document(
        run_id=args.run_id,
        case_id=args.case_id,
        report_payload=payload,
        discipline=(args.discipline or "").strip() or None,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {args.out} ({len(document['cases'][0]['findings'])} findings)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
