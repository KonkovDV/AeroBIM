"""Emit SIG-01 finding volume (not accuracy) from a gate JSON or the demo gate.

Writes only under ``.local/`` or outside the git tree.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.finding_volume import REPORT_PHRASE, volume_from_findings
from aerobim.domain.owner_files_inventory import require_local_only_output
from aerobim.tools.benchmark_project_package import repo_root


def _load_findings(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("gate JSON must be an object")
    raw = payload.get("findings") or []
    if not isinstance(raw, list):
        raise ValueError("findings must be a list")
    return [item for item in raw if isinstance(item, dict)]


def _load_lite_dir(path: Path) -> list[dict[str, Any]]:
    """Load findings-lite.json trees written by a local SIG-01 rerun."""

    rows: list[dict[str, Any]] = []
    for lite in sorted(path.rglob("findings-lite.json")):
        payload = json.loads(lite.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            rows.extend(item for item in payload if isinstance(item, dict))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate-json", type=Path, default=None)
    parser.add_argument("--findings-lite-dir", type=Path, default=None)
    parser.add_argument("--run-demo", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    root = repo_root()
    try:
        require_local_only_output(root, args.output)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.run_demo:
        from aerobim.tools.run_demo_ifc_acceptance_gate import run_demo_ifc_acceptance_gate

        gate = run_demo_ifc_acceptance_gate()
        findings = [item for item in (gate.get("findings") or []) if isinstance(item, dict)]
        claim_level = "fixture_only"
    elif args.findings_lite_dir is not None:
        findings = _load_lite_dir(args.findings_lite_dir)
        claim_level = "pack_volume_not_accuracy"
    elif args.gate_json is not None:
        findings = _load_findings(args.gate_json)
        claim_level = "pack_volume_not_accuracy"
    else:
        print("pass --run-demo, --gate-json, or --findings-lite-dir", file=sys.stderr)
        return 2
    payload = volume_from_findings(findings)
    payload["claim_level"] = claim_level
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "EXECUTED",
                "total": payload["total"],
                "report_phrase": payload.get("report_phrase", REPORT_PHRASE),
                "is_accuracy": False,
                "is_pack_processed": False,
                "is_customer_defect_list": False,
                "checkpoint": CHECKPOINT,
                "output": str(args.output),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
