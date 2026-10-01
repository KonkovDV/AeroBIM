"""Export the Kane IUA ledger to JSON / markdown evidence.

Does not close RT-001 / RT-002 / RT-003. Checkpoint GO (regulatory_measurement_mvp; customer_go false).
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from aerobim.domain.interpretation_use import ledger_payload, render_markdown


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--write-docs-evidence", action="store_true")
    args = parser.parse_args(argv)

    root = repo_root()
    payload = ledger_payload(generated_at=datetime.now(tz=UTC).isoformat())
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    out = args.output or (root / "artifacts" / "quality" / "interpretation-use-ledger.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    if args.write_docs_evidence:
        evidence = root / "docs" / "evidence" / "interpretation-use-ledger-latest.json"
        evidence.write_text(text, encoding="utf-8")
        markdown = root / "docs" / "quality" / "INTERPRETATION_USE_LEDGER_2026_08.md"
        markdown.write_text(render_markdown(payload), encoding="utf-8")
        print(f"docs_evidence={evidence}")
        print(f"docs_markdown={markdown}")
    print(
        json.dumps(
            {
                "status": "EXECUTED",
                "row_count": payload["row_count"],
                "checkpoint": payload["checkpoint"],
                "closes_rt001": False,
                "output": str(out),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
