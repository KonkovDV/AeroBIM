"""Ingest a BCFZIP from disk (export round-trip). Not CDE import. Not RT-008 T2."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from aerobim.infrastructure.adapters.bcf_consumers import (
    consume_bcf_zip_path,
    verify_bcf_zip_structure,
)

CLAIM_BOUNDARY = (
    "BCF file ingest is export round-trip / structural consume only; "
    "not CDE import; cde_import remains NOT_VERIFIED; not customer CDE evidence."
)


def ingest_payload(path: Path) -> dict[str, object]:
    archive = path.read_bytes()
    structural = verify_bcf_zip_structure(archive)
    topics = consume_bcf_zip_path(path)
    return {
        "artifact_type": "bcf_file_ingest",
        "path": str(path),
        "topic_count": len(topics),
        "topics": [
            {
                "topic_guid": topic.topic_guid,
                "title": topic.title,
                "has_viewpoint": topic.has_viewpoint,
                "selected_ifc_guids": list(topic.selected_ifc_guids),
            }
            for topic in topics
        ],
        "structural_ok": structural.ok,
        "version_id": structural.version_id,
        "cde_import": "NOT_VERIFIED",
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ingest a BCFZIP from disk (not CDE import)."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    if not args.input.is_file():
        print(f"Input not found: {args.input}", file=sys.stderr)
        return 1
    document = ingest_payload(args.input)
    serialized = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
