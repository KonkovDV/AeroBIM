"""Remove Co-authored-by trailers from stdin (git filter-branch --msg-filter)."""

import sys

lines = sys.stdin.read().splitlines(keepends=True)
out = [ln for ln in lines if not ln.strip().lower().startswith("co-authored-by:")]
sys.stdout.write("".join(out))
