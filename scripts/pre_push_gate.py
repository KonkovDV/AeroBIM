#!/usr/bin/env python3
"""Pre-push gate: run locally the fast checks CI runs, before pushing.

Mirrors the quick jobs in .github/workflows/ci.yml:
- ruff check + ruff format --check
- lint_claims (default, --full-docs, --matrix-guard, --claim-boundary-guard)
- runtime baseline README + committed-artifact drift (--check-readme --check-complete)
- docs metadata integrity, markdown links, ruff S-band inventory
- KT#2 handoff self-check

Usage from the repo root with the backend venv python:

    backend/.venv/Scripts/python.exe scripts/pre_push_gate.py          # fast gates
    backend/.venv/Scripts/python.exe scripts/pre_push_gate.py --full   # + mypy src

Full pytest/vitest stay in CI. If the baseline drift check fails, that is the
designed N-43 alarm (committed pin older than the tree); the script prints the
CI-artifact recovery steps instead of letting the push surprise you.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BACKEND = REPO / "backend"
PY = sys.executable

_STEPS_BASE: list[tuple[str, list[str], Path]] = [
    ("ruff check", [PY, "-m", "ruff", "check", "src", "tests"], BACKEND),
    ("ruff format --check", [PY, "-m", "ruff", "format", "--check", "src", "tests"], BACKEND),
    ("lint_claims", [PY, str(REPO / "scripts" / "lint_claims.py")], BACKEND),
    (
        "lint_claims --full-docs",
        [PY, str(REPO / "scripts" / "lint_claims.py"), "--full-docs"],
        BACKEND,
    ),
    (
        "lint_claims --matrix-guard",
        [PY, str(REPO / "scripts" / "lint_claims.py"), "--matrix-guard"],
        BACKEND,
    ),
    (
        "lint_claims --claim-boundary-guard",
        [PY, str(REPO / "scripts" / "lint_claims.py"), "--claim-boundary-guard"],
        BACKEND,
    ),
    (
        "runtime baseline drift",
        [
            PY,
            "-m",
            "aerobim.tools.export_runtime_baseline",
            "--check-readme",
            "--check-complete",
        ],
        BACKEND,
    ),
    (
        "docs metadata integrity",
        [PY, str(REPO / "scripts" / "check_docs_metadata_integrity.py")],
        REPO,
    ),
    ("markdown links", [PY, "-m", "aerobim.tools.check_markdown_links"], REPO),
    (
        "ruff S-band inventory",
        [PY, "scripts/verify_ruff_s_band_inventory.py"],
        BACKEND,
    ),
    ("kt2 handoff", [PY, "-m", "aerobim.tools.verify_kt2_handoff"], REPO),
]

_STEPS_FULL: list[tuple[str, list[str], Path]] = [
    ("mypy src", [PY, "-m", "mypy", "src"], BACKEND),
]

# CI checks out baseline-integrity with a shallow clone, so the N-43
# commits-behind counter cannot run there (unknown depth, warning only). What
# actually fails CI is LOC/metrics drift ("Baseline drift for ...") and broken
# README markers. Mirror that: fail on those, print commits-behind as a warning.
_BASELINE_SOFT_PREFIXES = ("baseline_commits_behind=", "baseline_stale_by_")

_BASELINE_RECOVERY = """\
Baseline LOC drift is the designed N-43 alarm: the committed pin is older than
the tree. Recovery:
  1. push this branch — baseline-integrity fails once and uploads
     the CI-attested artifact (expected, not a regression)
  2. download ci-runtime-baseline from that run into
     docs/evidence/runtime-baseline-latest.json and sync the README markers
  3. commit the refresh and push again; the second run goes green
Do NOT mint a baseline from a local pytest run (attested_by=ci only).\
"""


def _run(name: str, cmd: list[str], cwd: Path) -> tuple[bool, str]:
    start = time.monotonic()
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    elapsed = time.monotonic() - start
    output = ((proc.stdout or "") + (proc.stderr or "")).rstrip()
    if proc.returncode == 0:
        print(f"ok {name} ({elapsed:.1f}s)", flush=True)
        return True, ""
    if name == "runtime baseline drift":
        lines = [line for line in output.splitlines() if line.strip()]
        hard = [
            line for line in lines if not line.startswith(_BASELINE_SOFT_PREFIXES)
        ]
        if not hard:
            print(f"warn {name} ({elapsed:.1f}s) — commits-behind lag, invisible to CI", flush=True)
            print(output, flush=True)
            return True, ""
        print(f"FAIL {name} ({elapsed:.1f}s)", flush=True)
        print("\n".join(hard), flush=True)
        print("\n" + _BASELINE_RECOVERY, flush=True)
        return False, output
    print(f"FAIL {name} ({elapsed:.1f}s)", flush=True)
    print(output, flush=True)
    return False, output


def main(argv: list[str]) -> int:
    full = "--full" in argv
    steps = _STEPS_BASE + (_STEPS_FULL if full else [])
    failures = 0
    for name, cmd, cwd in steps:
        ok, _output = _run(name, cmd, cwd)
        if not ok:
            failures += 1
    if failures:
        print(f"\npre-push gate: {failures} failing step(s); push blocked", flush=True)
        return 1
    print("\npre-push gate: all fast CI checks green", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
