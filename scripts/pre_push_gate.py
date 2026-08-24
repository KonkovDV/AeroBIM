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

Full pytest/vitest stay in CI. LOC drift vs the committed pin is a warning
here (you cannot mint a CI-attested pin locally). CI ``baseline-integrity``
still fails until the attested artifact is committed. Broken README markers
still block the push.
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

# CI shallow-clones baseline-integrity, so the commits-behind counter is a
# warning there. LOC drift is also a *local* warning: recovery is "push, then
# commit the CI artifact". Blocking the push made that recovery impossible.
# Hard-fail only broken README markers / completeness, which you can fix here.
_BASELINE_SOFT_PREFIXES = (
    "baseline_commits_behind=",
    "baseline_stale_by_",
    "Baseline drift for ",
)

_BASELINE_RECOVERY = """\
Runtime baseline pin is older than the tree (LOC drift). This does not block
the local push. CI baseline-integrity will fail once and upload an attested
artifact. Commit that file into docs/evidence/runtime-baseline-latest.json,
sync README markers, push again. Do NOT mint a pin from local pytest
(attested_by=ci only).\
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
            print(f"warn {name} ({elapsed:.1f}s) — pin lags the tree (CI will refresh)", flush=True)
            print(output, flush=True)
            print("\n" + _BASELINE_RECOVERY, flush=True)
            return True, ""
        print(f"FAIL {name} ({elapsed:.1f}s)", flush=True)
        print("\n".join(hard), flush=True)
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
