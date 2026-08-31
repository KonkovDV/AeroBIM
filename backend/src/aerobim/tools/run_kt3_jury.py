"""KT#3 jury one-command: fixture gate + pack + tracker six tasks.

Fail-closed. Does not close RT. Fixture must stay passed=false.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.domain.kt3_jury import require_kt3_jury_gate
from aerobim.domain.kt3_without_customer import assemble_kt3_without_customer
from aerobim.tools.benchmark_project_package import repo_root
from aerobim.tools.run_kt3_without_customer import write_payload


def _load_gate(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"gate JSON must be an object: {path}")
    return payload


def assemble_kt3_jury(
    repo: Path,
    *,
    gate: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    jury = require_kt3_jury_gate(gate)
    pack = assemble_kt3_without_customer(repo, generated_at=generated_at)
    return {
        **jury,
        "generated_at": generated_at,
        "pack_checkpoint": pack["checkpoint"],
        "paper_objects": pack["paper_objects"],
        "typical_errors": pack["typical_errors"],
        "tracker": pack["tracker"],
        "tracker_eight": pack["tracker_eight"],
        "mik_m2_m8": pack["mik_m2_m8"],
        "demo_command": pack["demo_command"],
        "pack_command": pack["pack_command"],
        "jury_command": pack["jury_command"],
        "customer_files_expected": pack["customer_files_expected"],
        "nda_corpus_in_git": pack["nda_corpus_in_git"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-demo",
        action="store_true",
        help="Reuse an existing acceptance-gate.json (tests / reruns)",
    )
    parser.add_argument("--gate-json", type=Path, default=None)
    parser.add_argument("--generated-at", default=None)
    parser.add_argument("--write-docs-evidence", action="store_true")
    args = parser.parse_args(argv)
    root = repo_root()
    stamp = args.generated_at or datetime.now(tz=UTC).isoformat()

    if args.skip_demo:
        gate_path = args.gate_json or (
            root / "artifacts" / "ifc-acceptance-gate-demo" / "acceptance-gate.json"
        )
        if not gate_path.is_file():
            print(f"missing gate JSON: {gate_path}", file=sys.stderr)
            return 2
        gate = _load_gate(gate_path)
    else:
        from aerobim.tools.run_demo_ifc_acceptance_gate import run_demo_ifc_acceptance_gate

        gate = run_demo_ifc_acceptance_gate()

    payload = assemble_kt3_jury(root, gate=gate, generated_at=stamp)
    pack = assemble_kt3_without_customer(root, generated_at=stamp)
    write_payload(
        pack,
        artifacts_json=root / "artifacts" / "kt3-without-customer" / "latest.json",
        artifacts_md=root / "artifacts" / "kt3-without-customer" / "latest.md",
    )
    artifacts = root / "artifacts" / "kt3-jury" / "latest.json"
    artifacts.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    artifacts.write_text(text, encoding="utf-8")
    if args.write_docs_evidence:
        evidence = root / "docs" / "evidence" / "kt3-jury-2026-08.json"
        evidence.write_text(text, encoding="utf-8")
        write_payload(
            pack,
            artifacts_json=root / "docs" / "evidence" / "kt3-without-customer-latest.json",
            artifacts_md=root / "docs" / "evidence" / "kt3-without-customer-2026-08.md",
        )
        print(f"docs_evidence={evidence}")
    print(
        json.dumps(
            {
                "checkpoint": payload["checkpoint"],
                "passed": payload["passed"],
                "jury_rule_id": payload["jury_finding"]["rule_id"],
                "jury_ifc_guid": payload["jury_finding"]["ifc_guid"],
                "tracker_item_count": payload["tracker"]["item_count"],
                "typical_errors_confirmed": payload["typical_errors"][
                    "customer_confirmed_patterns"
                ],
                "closes_rt001": False,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
