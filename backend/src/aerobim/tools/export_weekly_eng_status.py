"""Export a weekly engineering status JSON (Task 7).

Commercial funnel numbers are **never invented** here — they stay owner-only
under ``.local/commercial-ops/``. This tool only aggregates public eng evidence:
runtime baseline, architecture inventory, Exp B KR share, adjudication plan
preview, and claim boundary.

Claim boundary: engineering readiness only. Checkpoint NO_GO. Not customer SLA.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _adjudication_preview() -> dict[str, Any] | None:
    try:
        from aerobim.tools.plan_adjudication_corpus import plan_adjudication_corpus
    except ImportError:
        return None
    return plan_adjudication_corpus()


def build_weekly_status(*, repo: Path | None = None) -> dict[str, Any]:
    root = repo or _repo_root()
    baseline = _load_json(root / "docs" / "evidence" / "runtime-baseline-latest.json") or {}
    eng = {
        "schema_version": "1.0.0",
        "artifact_type": "aerobim_weekly_eng_status",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "claim_boundary": (
            "Engineering weekly status only. No invented commercial funnel. "
            "Checkpoint NO_GO until RT-001/002/003. Fixture != customer accuracy."
        ),
        "checkpoint": "NO_GO",
        "rt_open": ["RT-001", "RT-002", "RT-003"],
        "runtime_baseline": {
            "commit_sha": baseline.get("commit_sha"),
            "schema_version": baseline.get("schema_version"),
            "metrics": baseline.get("metrics"),
            "architecture_inventory": baseline.get("architecture_inventory"),
            "quality_gates": baseline.get("quality_gates"),
        },
        "coverage_map": {
            "source": "docs/evidence/EXPERIMENT_B_TYPICAL_REMARKS_KR_COVERAGE_2026_08.md",
            "kr_detectable_share_approx": 0.167,
            "kr_detectable_rows": ["#2", "#3", "#4", "#24"],
            "kr_missing_attribute_rows": ["#9", "#10"],
            "claim_level": "AUTHOR_CLAIM_coverage_map_not_precision",
        },
        "adjudication_corpus_plan": _adjudication_preview(),
        "commercial_funnel": {
            "status": "OWNER_ONLY",
            "path": ".local/commercial-ops/outreach-log.md",
            "note": "Do not publish contacted/replied/demo zeros or invented counts to GH",
        },
        "next_levers": [
            "MISSING_ATTRIBUTE #9/#10 drawing_purpose roles (or stay conditional)",
            "RT-002 customer-approved norm pack",
            "RT-003 federated MEP scope memo",
            "Owner: PNST 909 pin; off-disk .local backup",
        ],
    }
    return eng


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write JSON (default: docs/evidence/weekly-eng-status-latest.json)",
    )
    parser.add_argument(
        "--print",
        action="store_true",
        help="Also print JSON to stdout",
    )
    args = parser.parse_args(argv)
    root = _repo_root()
    payload = build_weekly_status(repo=root)
    out = args.out or (root / "docs" / "evidence" / "weekly-eng-status-latest.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    out.write_text(text, encoding="utf-8")
    if args.print:
        print(text)
    else:
        print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
