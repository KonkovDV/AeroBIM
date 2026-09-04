"""Run the maximum licensed local pass on a Samolet quarantine copy.

Writes only under ``.local/`` or outside the git tree. Does not re-analyze
IFC (use an existing findings-lite tree). Does not parse RVT/NWD/.lir.
Does not raise the SPF cap. Checkpoint GO (regulatory_measurement_mvp; customer_go false).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from aerobim.domain.channel_local_max_pass import channel_local_max_pass_snapshot
from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.finding_volume import REPORT_PHRASE, volume_from_findings
from aerobim.domain.owner_files_inventory import require_local_only_output
from aerobim.tools.benchmark_project_package import repo_root
from aerobim.tools.pack_archive_overlap import probe_archives
from aerobim.tools.pack_probe import probe_pack, write_chat_summary, write_tracker_tsv
from aerobim.tools.run_finding_volume import _load_lite_dir
from aerobim.tools.scan_declared_calc_tokens import scan_declared_calc_tokens

CLAIM_BOUNDARY = (
    "Local maximum pass. Inventory + unsigned volume shape + token presence. "
    "Not pack processed. Not accuracy. Checkpoint GO (regulatory_measurement_mvp; customer_go false)."
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--findings-lite-dir", type=Path, default=None)
    parser.add_argument("--skip-hash", action="store_true")
    parser.add_argument("--progress", action="store_true")
    args = parser.parse_args(argv)
    root = repo_root()
    try:
        require_local_only_output(root, args.out)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if not args.pack.is_dir():
        print(f"pack directory missing: {args.pack}", file=sys.stderr)
        return 2
    args.out.mkdir(parents=True, exist_ok=True)
    snapshot = channel_local_max_pass_snapshot()
    _write_json(args.out / "git-safe-snapshot.json", snapshot)

    volume: dict[str, Any] | None = None
    if args.findings_lite_dir is not None and args.findings_lite_dir.is_dir():
        findings = _load_lite_dir(args.findings_lite_dir)
        volume = volume_from_findings(findings)
        volume["claim_level"] = "pack_volume_not_accuracy"
        _write_json(args.out / "sig01-volume.json", volume)

    tokens = scan_declared_calc_tokens(args.pack)
    _write_json(args.out / "sig06-token-scan.json", tokens)

    _archive_rows, archive_agg = probe_archives(args.pack)
    _write_json(args.out / "archive-aggregate.json", archive_agg)

    rows, aggregate = probe_pack(
        args.pack,
        progress=args.progress,
        compute_hash=not args.skip_hash,
    )
    _write_json(args.out / "pack-aggregate.json", aggregate)
    if not args.skip_hash:
        (args.out / "pack-local.json").write_text(
            json.dumps(rows, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        write_tracker_tsv(args.out / "pack-tracker.tsv", rows)
    write_chat_summary(args.out / "pack-chat-summary.md", aggregate)

    combined = {
        "artifact_type": "channel_local_max_pass_local",
        "claim_level": "coverage_map_only",
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "report_phrase": REPORT_PHRASE,
        "pack_processed": False,
        "is_accuracy": False,
        "publishable_finding_count": (volume or {}).get("publishable_finding_count", 0),
        "sig01_volume_total": None if volume is None else volume.get("total"),
        "sig01_by_volume_class": None if volume is None else volume.get("by_volume_class"),
        "pack_file_count": aggregate["file_count"],
        "pack_total_gib": aggregate["total_gib"],
        "pack_files_by_bucket": aggregate["files_by_bucket"],
        "archives_recommend_extract": archive_agg.get("recommend_extract_ifc_pdf"),
        "token_hits": tokens["hits"],
        "token_scanned_files": tokens["scanned_files"],
        "names_in_output": False,
        "hashes_in_output": False,
    }
    _write_json(args.out / "combined-aggregate.json", combined)
    print(json.dumps(combined, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
