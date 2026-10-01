#!/usr/bin/env python3
"""Fail if tracked paths look like private Red Team / recheck dumps (N-51 server gate)."""

from __future__ import annotations

import re
import subprocess
import sys

_BLOCKED = re.compile(
    r"(^|/)\.local(/|$)|internal-docs|aerobim_recheck|recheck_digest|recheck2_windows|"
    r"CORRECTIVE_AUDIT_CLASS_A",
    re.I,
)
# Public docs may legitimately use "red-team" in filenames.
_ALLOW = re.compile(r"^docs/(quality|red-team|architecture|security|tz)/", re.I)


def main() -> int:
    listed = subprocess.check_output(["git", "ls-files"], text=True, encoding="utf-8")
    bad = []
    for path in listed.splitlines():
        p = path.strip().replace("\\", "/")
        if not p or _ALLOW.search(p):
            continue
        if _BLOCKED.search(p):
            bad.append(p)
    print(f"tracked_paths_scanned private_marker_hits={len(bad)}")
    for path in bad:
        print(f"ERROR: tracked private marker path: {path}", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
