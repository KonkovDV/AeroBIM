"""Byte-token presence on office/PDF (SIG-06 CC-2/CC-4 pre-check).

Not extraction, not a solver, not calculation_correctness. Writes counts
only. Paths stay out of the aggregate. Checkpoint GO (regulatory_measurement_mvp; customer_go false).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.owner_files_inventory import require_local_only_output
from aerobim.tools.benchmark_project_package import repo_root
from aerobim.tools.pack_archive_overlap import iter_files

CLAIM_BOUNDARY = (
    "Byte-token presence in the first chunk of office/PDF files. "
    "Not a LIRA solver. Not CC-2 MATCH. Not конструкции пересчитаны. "
    "Compressed PDF streams may hide tokens. Checkpoint GO (regulatory_measurement_mvp; customer_go false)."
)

HEAD_BYTES = 512 * 1024
_SCAN_EXT = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".odt",
    ".ods",
    ".rtf",
    ".csv",
    ".txt",
}
_TOKEN_VARIANTS: dict[str, tuple[bytes, ...]] = {
    "B25": (b"B25", "В25".encode(), "B25".encode("utf-16le")),
    "B35": (b"B35", "В35".encode(), "B35".encode("utf-16le")),
    "LIRA": (b"LIRA", "ЛИРА".encode(), "ЛИРА".encode("utf-16le")),
    "rebar": ("арматур".encode(), "арматур".encode("utf-16le"), b"As,"),
    "deflection": ("прогиб".encode(), "прогиб".encode("utf-16le")),
    "load": ("нагруз".encode(), "нагруз".encode("utf-16le")),
}


def _head(path: Path, size: int = HEAD_BYTES) -> bytes:
    with path.open("rb") as handle:
        return handle.read(size)


def scan_declared_calc_tokens(root: Path) -> dict[str, Any]:
    """Count office/PDF files whose first chunk contains CC-related tokens."""

    scanned = 0
    skipped_ext = 0
    hits: Counter[str] = Counter()
    files_with_any = 0
    for path in iter_files(root):
        ext = path.suffix.lower()
        if ext not in _SCAN_EXT:
            skipped_ext += 1
            continue
        try:
            blob = _head(path)
        except OSError:
            continue
        scanned += 1
        matched = False
        for name, variants in _TOKEN_VARIANTS.items():
            if any(token in blob for token in variants):
                hits[name] += 1
                matched = True
        if matched:
            files_with_any += 1
    return {
        "artifact_type": "declared_calc_token_scan",
        "claim_level": "token_presence_not_solver",
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "native_lir": "not_implemented",
        "calculation_correctness": "NOT_IMPLEMENTED",
        "head_bytes": HEAD_BYTES,
        "scanned_files": scanned,
        "skipped_other_ext": skipped_ext,
        "files_with_any_token": files_with_any,
        "hits": dict(hits),
        "names_in_output": False,
        "hashes_in_output": False,
        "is_cc2_match": False,
        "is_solver": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        require_local_only_output(repo_root(), args.output)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    payload = scan_declared_calc_tokens(args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
