#!/usr/bin/env python3
"""Advisory commit-signature hygiene check for governance CI (RT-GOV-003)."""

from __future__ import annotations

import argparse
import subprocess
import sys


def _signed_commits(depth: int) -> tuple[int, int]:
    log = subprocess.check_output(
        ["git", "log", f"-{depth}", "--pretty=format:%G?"],
        text=True,
    )
    marks = [line.strip() for line in log.splitlines() if line.strip()]
    signed = sum(1 for mark in marks if mark == "G")
    return signed, len(marks)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--depth", type=int, default=20, help="Commits to inspect")
    parser.add_argument(
        "--min-ratio",
        type=float,
        default=0.0,
        help="Fail when signed/total is below this ratio (0 = advisory only)",
    )
    args = parser.parse_args()
    signed, total = _signed_commits(args.depth)
    ratio = (signed / total) if total else 0.0
    print(f"signed_commits={signed}/{total} ratio={ratio:.2f}")
    if args.min_ratio > 0 and ratio < args.min_ratio:
        print(
            f"ERROR: signed commit ratio {ratio:.2f} below required {args.min_ratio:.2f}",
            file=sys.stderr,
        )
        return 1
    if signed == 0:
        print(
            "NOTE: no GPG-signed commits in window; configure commit signing for provenance",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
