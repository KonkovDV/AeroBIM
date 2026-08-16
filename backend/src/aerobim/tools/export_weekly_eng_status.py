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


def _commercial_block(root: Path) -> dict[str, Any]:
    """Commercial funnel first. Never invent numbers; empty = explicit zero/missing."""

    path = root / ".local" / "commercial-ops" / "outreach-log.md"
    block: dict[str, Any] = {
        "status": "OWNER_ONLY",
        "path": ".local/commercial-ops/outreach-log.md",
        "contacted": None,
        "replied": None,
        "demo_agreed": None,
        "note": (
            "Do not publish contacted/replied/demo zeros or invented counts to GH. "
            "If outreach-log absent, mark data_missing — never soft-pedal."
        ),
    }
    if not path.is_file():
        block["data_status"] = "MISSING"
        block["print_as"] = "commercial block empty — no outreach-log.md"
        return block
    text = path.read_text(encoding="utf-8", errors="replace")
    block["data_status"] = "PRESENT_OWNER_FILE"
    block["bytes"] = len(text.encode("utf-8"))
    for key, needle in (
        ("contacted_marker", "связались"),
        ("replied_marker", "ответили"),
        ("demo_marker", "договорились о демо"),
    ):
        block[key] = needle in text.casefold()
    block["print_as"] = "commercial block present (counts OWNER-filled only)"
    return block


def build_weekly_status(*, repo: Path | None = None) -> dict[str, Any]:
    root = repo or _repo_root()
    baseline = _load_json(root / "docs" / "evidence" / "runtime-baseline-latest.json") or {}
    pnst_inv = _load_json(
        root / "docs" / "evidence" / "pnst909-22-scenario-ids-inventory-latest.json"
    )
    pnst_rt = _load_json(root / "docs" / "evidence" / "pnst909-22-scenario-runtime-latest.json")
    return {
        "schema_version": "1.2.0",
        "artifact_type": "aerobim_weekly_eng_status",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "claim_boundary": (
            "Engineering weekly status only. No invented commercial funnel. "
            "Checkpoint NO_GO until RF PD+expertise corpus, Samolet acceptance "
            "profile, and measured federated MEP. Fixture != customer accuracy."
        ),
        "checkpoint": "NO_GO",
        "rt_open": ["RT-001", "RT-002", "RT-003"],
        "commercial_funnel": _commercial_block(root),
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
            "ar_recount": "docs/evidence/EXPERIMENT_B_AR_SPB_AMUR_RECOUNT_2026_08.md",
            "claim_level": "AUTHOR_CLAIM_coverage_map_not_precision",
        },
        "pnst909_22_scenario_axis": {
            "inventory": "docs/evidence/pnst909-22-scenario-ids-inventory-latest.json",
            "runtime": "docs/evidence/pnst909-22-scenario-runtime-latest.json",
            "pairing": "docs/evidence/pnst909-22-scenario-pairing.json",
            "cli": "python -m aerobim.tools.run_pnst909_22_scenario_runtime",
            "tos_cite": "GO",
            "summary": (pnst_rt or pnst_inv or {}).get("summary"),
            "runtime_generated_at": (pnst_rt or {}).get("generated_at"),
            "runtime_status": "PARTIAL_18_OF_22_CLEAN",
            "ishigaki_cli": "python -m aerobim.tools.run_ishigaki_ids_bench_smoke",
            "ishigaki_evidence": "docs/evidence/ishigaki-ids-bench-smoke-latest.json",
        },
        "adjudication_corpus_plan": _adjudication_preview(),
        "next_levers": [
            "Exp A: 18/22 IDS runtime_clean published (ToS GO) — do not sell as precision",
            "PNST scenarios 3/18/21/22 still out_of_pack (no IDS in download)",
            "AR recount: SPb n=4 / Amur n=5 — do not merge organs into one %",
            "Norm-pack: edition field via samples/config/documentation-standard-edition.json",
            "MISSING_ATTRIBUTE #9/#10 drawing_purpose roles (or stay conditional)",
            "Owner DWG decision A/B/C: docs/tz/DWG_DECISION_OPTIONS_ABC_2026_08.md",
            "RT-002 Samolet-signed acceptance profile (public MOEXP IDS ≠ that profile)",
            "RT-003 measure public federated IFC (west_riverside / sixty5); not MEP delivered",
        ],
    }


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
