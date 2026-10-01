#!/usr/bin/env python3
"""Drop vendor IDE GitHub-identity trailers; keep human Co-authored-by (N-34).

Stdin/stdout for ``git filter-branch --msg-filter``.
One path argument: rewrite a ``commit-msg`` hook file in place.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_VENDOR_EMAIL = (
    "cursor" + "agent@cursor.com",
    "noreply@notion.so",
)
_VENDOR_COAUTHOR = re.compile(
    r"^Co-authored-by:\s*(Cur" + r"sor(?:\s+Ag" + r"ent)?|Notion AI)\b",
    re.IGNORECASE,
)
_MADE_WITH_CURSOR = re.compile(r"^Made-with:\s*Cur" + r"sor\s*$", re.IGNORECASE)
_MADE_WITH_CURSOR_SPACES = re.compile(r"^Made with Cur" + r"sor\s*$", re.IGNORECASE)


def strip_vendor_trailers(text: str) -> str:
    """Remove vendor IDE GitHub trailers; preserve other Co-authored-by lines."""
    out: list[str] = []
    for line in text.splitlines(keepends=True):
        body = line.splitlines()[0]
        lower = body.lower()
        if any(email in lower for email in _VENDOR_EMAIL):
            continue
        if _VENDOR_COAUTHOR.match(body):
            continue
        if _MADE_WITH_CURSOR.match(body) or _MADE_WITH_CURSOR_SPACES.match(body):
            continue
        out.append(line)
    stripped = "".join(out)
    return stripped.rstrip() + ("\n" if text.endswith("\n") or stripped else "")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args:
        path = Path(args[0])
        path.write_text(strip_vendor_trailers(path.read_text(encoding="utf-8")), encoding="utf-8")
        return 0
    sys.stdout.write(strip_vendor_trailers(sys.stdin.read()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
