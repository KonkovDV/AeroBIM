#!/usr/bin/env python3
"""Print the measured-clash slice recipe (WP-07) — no new protocol, reuse CLIs.

Does not claim "verified collisions". Language for the matrix:
  geometric AABB/IfcClash intersection P/R at n≈50, κ reported; not TZ >90%.

Usage (repo root or backend)::

    python scripts/run_clash_adjudication_slice.py
    python scripts/run_clash_adjudication_slice.py --check-tools
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_BACKEND = _REPO / "backend"

_STEPS = """
# Measured clash slice (apply protocol — do not invent)

1) Scope freeze (kickoff memo): finding_class=clash, strata, dual adjudicators.
   Template: samples/benchmarks/detection-precision/labels-customer-protocol-template.json
   Instruction: docs/pilot/EXPERT_LABELING_INSTRUCTION_2026.md
   SSOT: docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md

2) Geometry (intersection, not MEP AABB claim):
   cd backend && pip install -e ".[clash]"
   # analyze package with clash enabled → report JSON / evidence bundle

3) Export detections:
   aerobim-export-detections-from-report --report <report.json> --out detections.json

4) Dual-blind labels (CSV) + agreement:
   # fill samples/benchmarks/detection-precision/adjudication-template.csv
   aerobim-measure-adjudicator-agreement --csv <labels.csv>
   # gate: κ≥0.60 eng; target κ≥0.80 for this pilot pair

5) Build adjudicated labels + score:
   aerobim-build-detection-labels ...
   aerobim-evaluate-detection-precision --labels <labels.json> --detections <detections.json>
   # optional Wilson: python -m aerobim.tools.compute_quality_protocol_stats --tp .. --fp .. --fn ..

6) Matrix / claim boundary (1h):
   Replace clash accuracy cell with measured P/R + n + κ.
   Wording: "geometric intersection of extents, measured" — never "коллизия по ТЗ >90%".
   Run: python scripts/lint_claims.py --matrix-guard

Power note: planner prefers n≈62/111; n=50 is interim — report Wilson CI width honestly.
"""


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-tools",
        action="store_true",
        help="Verify detection-precision / agreement modules import",
    )
    args = parser.parse_args()
    print(_STEPS)
    if not args.check_tools:
        return 0

    sys.path.insert(0, str(_BACKEND / "src"))
    required = [
        "aerobim.tools.export_detections_from_report",
        "aerobim.tools.measure_adjudicator_agreement",
        "aerobim.tools.evaluate_detection_precision",
        "aerobim.tools.build_detection_labels",
    ]
    missing = [name for name in required if not _module_available(name)]
    if missing:
        print("MISSING:", ", ".join(missing), file=sys.stderr)
        return 1
    print("tools_ok", len(required))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
