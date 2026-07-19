# Backend dependency locks

Pinned installs for supply-chain honesty (RT-POST-09):

| File | Scope |
|------|--------|
| `requirements-lock.txt` | Runtime + `raster` (Docker image) |
| `requirements-dev-lock.txt` | Runtime + `dev` + `raster` (CI / local gates) |

Regenerate (Python 3.12, via [uv](https://github.com/astral-sh/uv)):

```bash
cd backend
uv pip compile --python 3.12 --extra=raster -o requirements-lock.txt pyproject.toml
uv pip compile --python 3.12 --extra=dev --extra=raster -o requirements-dev-lock.txt pyproject.toml
```

Install:

```bash
pip install -r requirements-dev-lock.txt
pip install -e . --no-deps
```
