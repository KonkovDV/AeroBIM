
"""Export the process-local IFC LRU RAM ceiling (RT16-RAM-01).

Ceiling = max_cached_models × max_ifc_bytes. Not a VM profile, not federated
RSS, not customer SLA. Does not close RT-003. Checkpoint GO (regulatory_measurement_mvp; customer_go false).
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.infrastructure.adapters.ifc_file_open import ifc_cache_ram_ceiling_payload


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--write-docs-evidence", action="store_true")
    args = parser.parse_args(argv)

    root = repo_root()
    payload = ifc_cache_ram_ceiling_payload(generated_at=datetime.now(tz=UTC).isoformat())
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    out = args.output or (root / "artifacts" / "quality" / "ifc-cache-ram-ceiling.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    if args.write_docs_evidence:
        evidence = root / "docs" / "evidence" / "ifc-cache-ram-ceiling-latest.json"
        evidence.write_text(text, encoding="utf-8")
        print(f"docs_evidence={evidence}")
    print(
        json.dumps(
            {
                "status": "EXECUTED",
                "ceiling_bytes": payload["ceiling_bytes"],
                "ceiling_gib": payload["ceiling_gib"],
                "measured_rss_delta_bytes": payload["measured_rss_delta_bytes"],
                "closes_rt003": False,
                "checkpoint": CHECKPOINT,
                "output": str(out),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
