#!/usr/bin/env bash
# Clone/laptop preflight using backend/.venv. Not the jury CLI itself.
set -euo pipefail
cd "$(dirname "$0")"
if [[ -x backend/.venv/bin/python ]]; then
  exec backend/.venv/bin/python -m aerobim.tools.check_local_launch "$@"
fi
if [[ -x backend/.venv/Scripts/python.exe ]]; then
  exec backend/.venv/Scripts/python.exe -m aerobim.tools.check_local_launch "$@"
fi
echo "backend/.venv not found. Run ./run-jury.sh or from backend/: python3.12 -m venv .venv"
echo "Do not use system python -m aerobim.tools.check_local_launch"
exit 1
