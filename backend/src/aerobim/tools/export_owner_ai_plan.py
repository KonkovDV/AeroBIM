"""Export the owner-AI plan snapshot to docs/evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aerobim.domain.owner_ai_plan import plan_snapshot


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--write-docs-evidence", action="store_true")
    args = parser.parse_args(argv)

    payload = plan_snapshot()
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    root = repo_root()
    out = args.output or (root / "artifacts" / "quality" / "owner-ai-plan-execution.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    if args.write_docs_evidence:
        evidence = root / "docs" / "evidence" / "owner-ai-plan-execution-2026-08.json"
        evidence.write_text(text, encoding="utf-8")
        print(f"docs_evidence={evidence}")
    print(
        json.dumps(
            {
                "status": "EXECUTED",
                "checkpoint": payload["checkpoint"],
                "item_count": payload["item_count"],
                "agent_done_count": payload["agent_done_count"],
                "owner_blocked_count": payload["owner_blocked_count"],
                "closes_rt001": False,
                "output": str(out),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
