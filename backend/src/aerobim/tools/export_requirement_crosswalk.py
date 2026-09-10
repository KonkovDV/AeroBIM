"""Export a requirement-row crosswalk. Human labels in; no auto-match."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from aerobim.domain.requirement_crosswalk import build_requirement_crosswalk


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Requirement crosswalk (not accuracy)")
    parser.add_argument("--rows-json", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-csv", type=Path, default=None)
    parser.add_argument("--adjudicators", type=int, default=1)
    args = parser.parse_args(argv)
    payload = json.loads(args.rows_json.read_text(encoding="utf-8"))
    rows = payload.get("rows") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise SystemExit("rows-json must be a list or {rows: []}")
    crosswalk = build_requirement_crosswalk(rows, adjudicators=args.adjudicators)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(
        json.dumps(crosswalk, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if args.out_csv is not None:
        args.out_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.out_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "row_id",
                    "machine_verifiability",
                    "assigned_by",
                    "coverage_status",
                    "check_family",
                    "matched_finding_ids",
                ],
            )
            writer.writeheader()
            for row in crosswalk["rows"]:
                writer.writerow(
                    {
                        "row_id": row.get("row_id"),
                        "machine_verifiability": row.get("machine_verifiability"),
                        "assigned_by": row.get("assigned_by"),
                        "coverage_status": row.get("coverage_status"),
                        "check_family": row.get("check_family"),
                        "matched_finding_ids": "",
                    }
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
