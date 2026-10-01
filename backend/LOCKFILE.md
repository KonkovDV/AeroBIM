# Backend dependency locks

Pinned installs for supply-chain honesty (RT-POST-09 / RTATOM A2.5):

| File | Scope |
|------|--------|
| `requirements-lock.txt` | Runtime + `raster` (Docker image; **no** PyMuPDF). Linux/CI. Contains `uvloop`. |
| `requirements-dev-lock.txt` | Runtime + `dev` + `raster` + `pdf-agpl` (CI / local Linux gates; optional AGPL tools) |
| `requirements-win-lock.txt` | Runtime + `dev` + `raster` for `x86_64-pc-windows-msvc`. **No** `uvloop`, **no** PyMuPDF. Online hashed install, not air-gap. |

Regenerate (Python 3.12, via [uv](https://github.com/astral-sh/uv)):

```bash
cd backend
uv pip compile --python 3.12 --python-platform x86_64-manylinux_2_31 --generate-hashes --extra=raster -o requirements-lock.txt pyproject.toml
uv pip compile --python 3.12 --python-platform x86_64-manylinux_2_31 --generate-hashes --extra=dev --extra=raster --extra=pdf-agpl -o requirements-dev-lock.txt pyproject.toml
uv pip compile --python 3.12 --python-platform x86_64-pc-windows-msvc --generate-hashes --extra=dev --extra=raster -o requirements-win-lock.txt pyproject.toml
```

Linux/CI locks target `x86_64-manylinux_2_31` so CI (ubuntu) and Docker stay aligned. The Windows lock includes Windows-only extras (e.g. `colorama`) and omits `uvloop`.
Install (Linux/CI):

```bash
python -m pip install --upgrade "pip==25.2"
pip install --require-hashes -r requirements-dev-lock.txt
pip install -e . --no-deps
```

Windows hashed path (optional, needs PyPI — **not** the closed contour):

```powershell
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-win-lock.txt
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
```

First-clone jury recipe remains `.\.venv\Scripts\python.exe -m pip install -e ".[dev,raster]"` (README [Try it](../README.md#try-it)). Optional `pdf-agpl` is not required for the KT#2 overlay (pypdfium2). Closed contour is Docker image-track, not a wheelhouse and not this Windows lock.

Residual: the initial `pip==25.2` bootstrap wheel is not hash-verified; runtime/dev dependencies from the lockfiles are.
