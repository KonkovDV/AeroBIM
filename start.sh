#!/usr/bin/env bash
# Review shell (API + Vite). Not the jury CLI. Not Next.js.
# From the clone root: ./start.sh
# Vite: 127.0.0.1:5173   API: 127.0.0.1:8080
set -euo pipefail
cd "$(dirname "$0")"
python_posix="backend/.venv/bin/python"
python_win="backend/.venv/Scripts/python.exe"
if [[ -x "$python_posix" ]]; then
  exec "$python_posix" -m aerobim.tools.run_review_stand "$@"
fi
if [[ -x "$python_win" ]]; then
  exec "$python_win" -m aerobim.tools.run_review_stand "$@"
fi
echo "backend/.venv not found. Run ./run-jury.sh first, or from AeroBIM/backend:"
echo "  python3.12 -m venv .venv"
echo "  python -m pip install -e \".[dev,raster]\""
echo "Review shell needs Node 20+. Jury CLI does not. customer_go false."
exit 1
