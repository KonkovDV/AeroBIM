# Backend dependency locks

Pinned installs for supply-chain honesty (RT-POST-09 / RTATOM A2.5):

| File | Scope |
|------|--------|
| `requirements-lock.txt` | Runtime + `raster` (Docker image) |
| `requirements-dev-lock.txt` | Runtime + `dev` + `raster` (CI / local gates) |

Regenerate (Python 3.12, Linux/CI target via [uv](https://github.com/astral-sh/uv)):

```bash
cd backend
uv pip compile --python 3.12 --python-platform x86_64-manylinux_2_31 --generate-hashes --extra=raster -o requirements-lock.txt pyproject.toml
uv pip compile --python 3.12 --python-platform x86_64-manylinux_2_31 --generate-hashes --extra=dev --extra=raster -o requirements-dev-lock.txt pyproject.toml
```

Locks target `x86_64-manylinux_2_31` so CI (ubuntu) and Docker stay aligned; Windows-only extras (e.g. `colorama`) are intentionally absent.
Install:

```bash
python -m pip install --upgrade "pip==25.2"
pip install --require-hashes -r requirements-dev-lock.txt
pip install -e . --no-deps
```

Residual: the initial `pip==25.2` bootstrap wheel is not hash-verified; runtime/dev dependencies from the lockfiles are.
