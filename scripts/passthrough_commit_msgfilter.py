#!/usr/bin/env python3
"""Stdin/stdout passthrough for git commit-msg filters (N-34). Do not strip Co-authored-by."""

from __future__ import annotations

import sys


def main() -> int:
    sys.stdout.write(sys.stdin.read())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
