from __future__ import annotations

import argparse
import json
from pathlib import Path

from aerobim.application.use_cases.analyze_project_package import (
    build_openrebar_provenance_digest,
)


def compute_openrebar_provenance_digest(report_path: Path) -> dict[str, object]:
    resolved_path = report_path.resolve()
    if not resolved_path.exists():
        raise FileNotFoundError(resolved_path)

    try:
        payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid OpenRebar reinforcement report JSON: {resolved_path}") from exc

    if not isinstance(payload, dict):
        raise ValueError("OpenRebar reinforcement report must be a JSON object")

    metadata_payload = payload.get("metadata")
    metadata = metadata_payload if isinstance(metadata_payload, dict) else {}

    return {
        "reinforcement_report_path": str(resolved_path),
        "provenance_digest": build_openrebar_provenance_digest(payload),
        "contract_id": payload.get("contractId"),
        "schema_version": payload.get("schemaVersion"),
        "project_code": metadata.get("projectCode"),
        "slab_id": metadata.get("slabId"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build OpenRebar provenance digest from canonical reinforcement report"
    )
    parser.add_argument("report_path", type=Path, help="Path to OpenRebar *.result.json")
    args = parser.parse_args()

    payload = compute_openrebar_provenance_digest(args.report_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
