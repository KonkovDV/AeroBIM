#!/usr/bin/env python3
"""One-command review shell (API + Vite).

From the repo root, with ``backend/.venv`` already created::

    python scripts/run_review_shell.py

Linux/macOS: ``./start.sh``. Windows: ``.\\start.bat``.
Vite is ``127.0.0.1:5173``; API is ``127.0.0.1:8080``. Not Next.js.

If the frontend tree was copied without backend, set ``AEROBIM_BACKEND_DIR``
to the clone's ``backend`` directory (do not leave the API only under ``/tmp``).

Not the jury CLI (``python -m aerobim.tools.run_kt3_jury``).
Not a customer pack. Checkpoint GO; customer_go false.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]


def resolved_backend_dir(repo: Path = _REPO) -> Path:
    override = (os.environ.get("AEROBIM_BACKEND_DIR") or "").strip()
    if override and repo == _REPO:
        return Path(override).expanduser().resolve()
    return repo / "backend"


def backend_venv_python(repo: Path = _REPO) -> Path:
    backend = resolved_backend_dir(repo)
    candidates = (
        backend / ".venv" / "Scripts" / "python.exe",
        backend / ".venv" / "bin" / "python",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "backend/.venv not found. AeroBIM API lives in <clone>/backend "
        "(Windows: .venv\\Scripts\\python.exe; Linux: .venv/bin/python), "
        "not a frontend-only tree. Set AEROBIM_BACKEND_DIR if needed. "
        'From AeroBIM/backend: py -3.12 -m venv .venv && pip install -e ".[dev,raster]"'
    )


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    child_env = os.environ.copy()
    child_env.setdefault("AEROBIM_BACKEND_DIR", str((_REPO / "backend").resolve()))
    child_env.setdefault("AEROBIM_FRONTEND_DIR", str((_REPO / "frontend").resolve()))
    try:
        python = backend_venv_python()
    except FileNotFoundError as error:
        sys.stderr.write(f"{error}\n")
        return 1
    return subprocess.call(
        [str(python), "-m", "aerobim.tools.run_review_stand", *args],
        cwd=str(resolved_backend_dir()),
        env=child_env,
    )


if __name__ == "__main__":
    raise SystemExit(main())
