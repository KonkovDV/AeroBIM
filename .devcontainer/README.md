# Dev Container

Optional contributor environment (VS Code / Codespaces). Not the jury CLI. Checkpoint `GO`; `customer_go` false.

Python 3.12, Node 22, extras `.[dev,raster]`. Ports 8080 / 5173. Port 3000 is ignored (Next.js). `AEROBIM_ENV=development`. Do not set `AEROBIM_SIGNOFF_PROFILE=customer_pilot`.

Sitting-member track remains `python -m aerobim.tools.run_kt3_jury` from `backend/` after the post-create venv. Closed contour is Docker image-track, not this container and not a pip wheelhouse.
