# Offline deployment (2026)

**Claim level:** Docker **image-track** eng evidence (CI `offline-bundle-smoke`).  
**Owner note (2026-08-01):** bare-metal without Docker is **not required** while Docker offline works.  
**Refresh (2026-08-03, RT-019):** `build` also writes `INSTALL_OFFLINE.md`, `MIRROR_CHECKLIST.md`, and `sbom-spdx-lite.json` (lockfile SPDX-lite).  
**Checked:** 2026-07-31 / 2026-08-01 / 2026-08-03 against `aerobim.tools.offline_bundle`.

## What is VERIFIED

Commands (from `backend/`):

```bash
python -m aerobim.tools.offline_bundle build
python -m aerobim.tools.offline_bundle verify
python -m aerobim.tools.offline_bundle smoke
python -m aerobim.tools.offline_bundle sbom       # SPDX-lite from requirements-lock.txt
python -m aerobim.tools.offline_bundle wheelhouse  # exit 2 — DEFERRED honesty artifact
```

`smoke` path: `docker rmi` tag → `docker load` from tar → run container `--network none` → health + capabilities HTTP checks.

`wheelhouse` writes `artifacts/offline-bundle/wheelhouse-DEFERRED.json` and exits **2** — bare-metal pip wheelhouse is explicitly DEFERRED, not verified.

CI: `.github/workflows/ci.yml` job `offline-bundle-smoke` (on `main`).

## Bundle contents (after `build`)

| File | Role |
|---|---|
| `aerobim-backend-image.tar` | `docker save` image |
| `requirements-*.txt` + `Dockerfile` | hash-locked rebuild evidence |
| `sbom-spdx-lite.json` | lockfile package pins + SHA256 (not full CycloneDX graph) |
| `INSTALL_OFFLINE.md` | air-gap load steps |
| `MIRROR_CHECKLIST.md` | Docker Hub / PyPI / GitHub / GitVerse operator notes |
| `BUNDLE_MANIFEST.json` | sha256 map |

## What is NOT REQUIRED (deferred)

| Item | Status |
|---|---|
| Bare-metal wheelhouse install without Docker | **DEFERRED** — owner: Docker path sufficient |
| Live GitVerse mirror of this repo | Operator checklist only — **not** product-claimed |
| Full npm cache offline frontend rebuild inside bundle | UNKNOWN |
| Hugging Face / cloud LLM in offline mode | N/A — default deny; advisory optional |

## Capabilities expected offline

Deterministic analyze path without external LLM/OCR extras may run with skipped/missing optional capabilities. Do not claim full feature parity offline without the smoke artifact for that build.

## Forbidden claims

«Работает в любом закрытом контуре без Docker» — запрещено (bare-metal not proven; Docker-track only).  
«GitVerse mirror готов» / «полный CycloneDX SBOM» — запрещено без отдельного evidence.
