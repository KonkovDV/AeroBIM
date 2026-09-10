#!/usr/bin/env python3
"""One-command IT-mentor review shell (API + Vite).

From the repo root, with ``backend/.venv`` already created::

    python scripts/run_review_shell.py

Not the jury CLI (``python -m aerobim.tools.run_kt3_jury``).
Not a customer pack. Checkpoint GO; customer_go false.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]


def backend_venv_python(repo: Path = _REPO) -> Path:
    candidates = (
        repo / "backend" / ".venv" / "Scripts" / "python.exe",
        repo / "backend" / ".venv" / "bin" / "python",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "backend/.venv not found. From AeroBIM/backend: "
        'py -3.12 -m venv .venv && pip install -e ".[dev,raster]"'
    )


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        python = backend_venv_python()
    except FileNotFoundError as error:
        sys.stderr.write(f"{error}\n")
        return 1
    return subprocess.call(
        [str(python), "-m", "aerobim.tools.run_it_mentor_stand", *args]
    )


if __name__ == "__main__":
    raise SystemExit(main())
