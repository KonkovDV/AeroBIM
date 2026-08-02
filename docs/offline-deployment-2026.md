# Offline deployment (2026)

**Claim level:** Docker **image-track** eng evidence (CI `offline-bundle-smoke`).  
**Owner note (2026-08-01):** bare-metal without Docker is **not required** while Docker offline works.  
**Checked:** 2026-07-31 / 2026-08-01 against `aerobim.tools.offline_bundle`.

## What is VERIFIED

Commands (from `backend/`):

```bash
python -m aerobim.tools.offline_bundle build
python -m aerobim.tools.offline_bundle verify
python -m aerobim.tools.offline_bundle smoke
python -m aerobim.tools.offline_bundle wheelhouse  # exit 2 — DEFERRED honesty artifact
```

`smoke` path: `docker rmi` tag → `docker load` from tar → run container `--network none` → health + capabilities HTTP checks.

`wheelhouse` writes `artifacts/offline-bundle/wheelhouse-DEFERRED.json` and exits **2** — bare-metal pip wheelhouse is explicitly DEFERRED, not verified.

CI: `.github/workflows/ci.yml` job `offline-bundle-smoke` (on `main`).

## What is NOT REQUIRED (deferred)

| Item | Status |
|---|---|
| Bare-metal wheelhouse install without Docker | **DEFERRED** — owner: Docker path sufficient; `python -m aerobim.tools.offline_bundle wheelhouse` writes honesty artifact and exits 2 |
| Full npm cache offline frontend rebuild inside bundle | UNKNOWN / check current bundle manifest |
| Hugging Face / cloud LLM in offline mode | N/A — default deny; advisory optional |

## Capabilities expected offline

Deterministic analyze path without external LLM/OCR extras may run with skipped/missing optional capabilities. Do not claim full feature parity offline without the smoke artifact for that build.

## Forbidden claims

«Работает в любом закрытом контуре без Docker» — запрещено (bare-metal not proven; Docker-track only).
