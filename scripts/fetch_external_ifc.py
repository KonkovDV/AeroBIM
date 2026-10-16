#!/usr/bin/env python3
"""Download the large real IFC models listed in scripts/large_real_ifc_manifest.json.

Each file is verified against its pinned SHA-256 and size; a mismatch deletes
the download and exits non-zero. Files are never committed to the repo.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "scripts" / "large_real_ifc_manifest.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(dest: Path, manifest: Path = MANIFEST) -> list[Path]:
    spec = json.loads(manifest.read_text(encoding="utf-8"))
    dest.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for item in spec["files"]:
        if not item["url"].startswith("https://"):
            raise SystemExit(f"{item['name']}: manifest URL must be https")
        target = dest / item["name"]
        if not (target.is_file() and _sha256(target) == item["sha256"]):
            partial = target.with_suffix(target.suffix + ".part")
            with (
                urllib.request.urlopen(item["url"], timeout=120) as resp,
                partial.open("wb") as out,
            ):
                while chunk := resp.read(1024 * 1024):
                    out.write(chunk)
            actual = _sha256(partial)
            if actual != item["sha256"] or partial.stat().st_size != item["size"]:
                partial.unlink(missing_ok=True)
                raise SystemExit(
                    f"{item['name']}: SHA-256/size mismatch (got {actual}, "
                    f"{partial.stat().st_size if partial.exists() else '?'} bytes); refusing to use it"
                )
            partial.replace(target)
        print(f"{item['name']} sha256={item['sha256']} size={item['size']}")
        paths.append(target)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    fetch(args.dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
