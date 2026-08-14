"""Compare two package DocumentIdentity lists (TZ row 28 fixture path).

Not CDE version management. Not a new DI port. Does not close RT-001/002/003.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from aerobim.domain.ingestion import (
    PACKAGE_IDENTITY_CLAIM_BOUNDARY,
    compare_package_document_identities,
    identities_from_mapping,
)
from aerobim.domain.models import ValidationIssue


def _load_side(payload: dict[str, Any], key: str) -> list[dict[str, object]]:
    raw = payload.get(key)
    if not isinstance(raw, list):
        raise ValueError(f"{key} must be a JSON array")
    return [item for item in raw if isinstance(item, dict)]


def _issue_row(issue: ValidationIssue) -> dict[str, object]:
    return {
        "rule_id": issue.rule_id,
        "severity": issue.severity.value,
        "conflict_kind": (
            issue.conflict_kind.value if issue.conflict_kind is not None else None
        ),
        "source_id": issue.source_id,
        "expected_value": issue.expected_value,
        "observed_value": issue.observed_value,
        "message": issue.message,
    }


def compare_payload(payload: dict[str, Any]) -> dict[str, Any]:
    previous = identities_from_mapping(_load_side(payload, "previous"))
    current = identities_from_mapping(_load_side(payload, "current"))
    issues = compare_package_document_identities(previous, current)
    return {
        "artifact_type": "package_identity_compare",
        "schema": str(payload.get("schema") or "aerobim.package_identity_compare.v1"),
        "issue_count": len(issues),
        "error_count": sum(1 for issue in issues if issue.severity.value == "error"),
        "issues": [_issue_row(issue) for issue in issues],
        "claim_boundary": PACKAGE_IDENTITY_CLAIM_BOUNDARY,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "cde_version_management": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compare previous vs current package document identities "
            "(fixture/engine only — not CDE)."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="JSON with previous/current arrays",
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    path = args.input.resolve()
    if not path.is_file():
        print(f"Input not found: {path}", file=sys.stderr)
        return 1
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        print("Input root must be a JSON object", file=sys.stderr)
        return 1
    document = compare_payload(payload)
    serialized = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
