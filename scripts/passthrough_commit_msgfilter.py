#!/usr/bin/env python3
"""Stdin/stdout commit-msg filter: keep human Co-authored-by; drop vendor IDE trailers."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from strip_vendor_commit_trailers import strip_vendor_trailers  # noqa: E402


def main() -> int:
    sys.stdout.write(strip_vendor_trailers(sys.stdin.read()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
