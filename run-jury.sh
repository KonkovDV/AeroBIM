#!/usr/bin/env bash
# One-command jury CLI from the clone root. Not the review shell.
set -euo pipefail
cd "$(dirname "$0")/backend"
echo "AeroBIM jury CLI. Node is not required. customer_go false."
echo "summary.passed=false on the fixture pack is expected."
export PIP_DISABLE_PIP_VERSION_CHECK=1

if [[ ! -x .venv/bin/python ]]; then
  if command -v python3.12 >/dev/null 2>&1; then
    echo "Creating backend/.venv with python3.12 ..."
    python3.12 -m venv .venv
  else
    echo "python3.12 not found. Install CPython 3.12."
    exit 1
  fi
fi

if ! .venv/bin/python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)"; then
  echo "backend/.venv is not CPython 3.12. Delete it and re-run."
  exit 1
fi

.venv/bin/python -m pip install -U pip
.venv/bin/python -m pip install -e ".[dev,raster]"
.venv/bin/python -m aerobim.tools.check_local_launch
.venv/bin/python -m aerobim.tools.run_kt3_jury
echo "Done. expected summary.passed=false. customer_go false."
