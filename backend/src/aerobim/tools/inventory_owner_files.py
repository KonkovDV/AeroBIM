"""Write owner-disk files/ inventory under .local/ only.

Does not parse IFC. Does not raise the 256 MiB cap. Does not close RT.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from aerobim.domain.owner_files_inventory import (
    DEFAULT_IFC_CAP_BYTES,
    public_rehearsal_snapshot,
    rehearsal_differs,
    require_local_only_output,
    scan_owner_files,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Owner files tree (default: repo/files or AEROBIM_OWNER_FILES)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Must be under <repo>/.local/ or outside the git tree",
    )
    parser.add_argument(
        "--include-names",
        action="store_true",
        help="Include folder labels (local only; never commit)",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    try:
        require_local_only_output(root, args.output)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    tree = args.root
    if tree is None:
        env = os.environ.get("AEROBIM_OWNER_FILES", "").strip()
        tree = Path(env) if env else (root / "files")
    scan = scan_owner_files(tree, ifc_cap_bytes=DEFAULT_IFC_CAP_BYTES, include_names=args.include_names)
    payload = {
        **scan,
        "public_rehearsal": public_rehearsal_snapshot(),
        "differs_from_public_rehearsal": rehearsal_differs(scan),
        "names_must_not_enter_git": True,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": scan.get("status"),
                "output": str(args.output),
                "file_count": scan.get("file_count"),
                "ifc_count": scan.get("ifc_count"),
                "differs_from_public_rehearsal": payload["differs_from_public_rehearsal"],
                "checkpoint": "NO_GO",
                "closes_rt001": False,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
