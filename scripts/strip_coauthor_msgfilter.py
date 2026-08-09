"""Pass-through msg-filter (historical rewrite tool).

Previously stripped Co-authored-by trailers. That rewrote provenance metadata and
is no longer permitted. This script now copies stdin to stdout unchanged.
"""

from __future__ import annotations

import sys

sys.stdout.write(sys.stdin.read())
