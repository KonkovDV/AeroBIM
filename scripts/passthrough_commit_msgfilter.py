"""Historical commit-msg filter — now a passthrough (N-34 / A-3).

Previously this module stripped Co-authored-by trailers, rewriting provenance
metadata. That behavior was removed on 2026-08-09. Keep the file only as a
dated tombstone for anyone still invoking the old path; prefer not calling it.
"""

from __future__ import annotations

import sys

sys.stdout.write(sys.stdin.read())
