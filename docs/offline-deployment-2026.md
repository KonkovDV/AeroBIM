# Offline deployment (2026)

**Claim level:** Docker **image-track** eng evidence (CI `offline-bundle-smoke`).  
**И1 status (2026-08-08):** **CLOSED** — Docker closed-contour verified (`closed-contour --smoke`).  
**Owner decision:** bare-metal wheelhouse is **OUT_OF_SCOPE** while Docker offline works.  
**Ops runbook:** [`docs/ops/OFFLINE_CLOSED_CONTOUR_DOCKER_2026_08.md`](ops/OFFLINE_CLOSED_CONTOUR_DOCKER_2026_08.md)  
**Checked:** 2026-08-08 against `aerobim.tools.offline_bundle`.

## What is VERIFIED

Commands (from `backend/`):

```bash
python -m aerobim.tools.offline_bundle build
python -m aerobim.tools.offline_bundle verify
python -m aerobim.tools.offline_bundle smoke
python -m aerobim.tools.offline_bundle closed-contour --smoke   # И1 operator gate
python -m aerobim.tools.offline_bundle sbom
python -m aerobim.tools.offline_bundle wheelhouse  # exit 2 — OUT_OF_SCOPE honesty artifact
```

`smoke` path: `docker rmi` tag → `docker load` from tar → run container `--network none` → health + capabilities HTTP checks.

`wheelhouse` writes `wheelhouse-OUT_OF_SCOPE.json` (exit **2**) — bare-metal pip is not required for И1.

CI: `.github/workflows/ci.yml` job `offline-bundle-smoke` (on `main`).

## Bundle contents (after `build`)

| File | Role |
|---|---|
| `aerobim-backend-image.tar` | `docker save` image |
| `requirements-*.txt` + `Dockerfile` | hash-locked rebuild evidence |
| `sbom-spdx-lite.json` | lockfile package pins + SHA256 |
| `INSTALL_OFFLINE.md` | air-gap load steps |
| `install_offline.sh` / `install_offline.ps1` | one-click load + run |
| `MIRROR_CHECKLIST.md` | Docker Hub / PyPI / GitHub / GitVerse operator notes |
| `BUNDLE_MANIFEST.json` | sha256 map |

## What is OUT OF SCOPE (not blocking И1)

| Item | Status |
|---|---|
| Bare-metal wheelhouse install without Docker | **OUT_OF_SCOPE** — Docker path closes И1 |
| Live GitVerse mirror of this repo | Operator checklist only |
| Full npm cache offline frontend rebuild inside bundle | UNKNOWN |
| Hugging Face / cloud LLM in offline mode | N/A — default deny |

## Capabilities expected offline

Deterministic analyze path without external LLM/OCR extras may run with skipped/missing optional capabilities. Do not claim full feature parity offline without the smoke artifact for that build.

## Forbidden claims

«Работает в любом закрытом контуре без Docker» — запрещено (bare-metal OUT_OF_SCOPE).  
«GitVerse mirror готов» / «полный CycloneDX SBOM» — запрещено без отдельного evidence.
