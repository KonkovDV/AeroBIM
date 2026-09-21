#!/usr/bin/env bash
# Contributor environment. Not the jury laptop track. Checkpoint GO; customer_go false.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
python3 -m venv .venv
.venv/bin/python -m pip install -U pip
.venv/bin/python -m pip install -e ".[dev,raster]"
cd "$ROOT/frontend"
npm ci
echo "Dev Container extras are .[dev,raster]. Jury CLI: python -m aerobim.tools.run_kt3_jury from backend/."
echo "Do not export a closed sign-off profile. Closed contour is Docker, not a wheelhouse."
