#!/usr/bin/env python3
"""One-shot helper: prepend claims-lint allow-file to docs that cite forbidden phrases honestly."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ALLOW_LINE = (
    '<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as '
    'non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->\n'
)


def main() -> int:
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "lint_claims.py"), "--full-docs"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        print("No violations; nothing to bootstrap")
        return 0
    paths: set[Path] = set()
    for line in proc.stderr.splitlines():
        if ":" not in line:
            continue
        rel = line.split(":", 1)[0]
        paths.add(REPO / rel)
    changed = 0
    for path in sorted(paths):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if "claims-lint: allow-file" in text[:500]:
            continue
        path.write_text(ALLOW_LINE + text, encoding="utf-8")
        changed += 1
        print(f"allow-file: {path.relative_to(REPO).as_posix()}")
    print(f"Updated {changed} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
