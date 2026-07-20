"""CLI/export helper for cross-revision finding deltas (engineering only)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from aerobim.domain.finding_revision_compare import (
    compare_findings_across_revisions,
    export_finding_revision_delta_document,
)


def _load_issues(path: Path) -> tuple[list[dict[str, Any]], str | None]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: root must be a JSON object")
    revision = payload.get("revision")
    if revision is not None and not isinstance(revision, str):
        revision = str(revision)
    issues = payload.get("issues")
    if not isinstance(issues, list):
        raise ValueError(f"{path}: issues must be an array")
    return [item for item in issues if isinstance(item, dict)], revision


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare findings across two report JSON revisions "
            "(engineering harness — not customer pack evidence)"
        )
    )
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    previous_issues, previous_revision = _load_issues(args.previous)
    current_issues, current_revision = _load_issues(args.current)
    deltas = compare_findings_across_revisions(previous_issues, current_issues)
    document = export_finding_revision_delta_document(
        previous_revision=previous_revision,
        current_revision=current_revision,
        deltas=deltas,
    )
    serialized = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(serialized, encoding="utf-8")
        temporary.replace(args.output)
    else:
        sys.stdout.write(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
