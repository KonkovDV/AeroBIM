# Offline deployment (2026)

**Claim level:** image-track eng evidence; **not** bare-metal offline-ready.  
**Checked:** 2026-07-31 against `aerobim.tools.offline_bundle`.

## What is VERIFIED (prior cycle + code present)

Commands (from `backend/`):

```bash
python -m aerobim.tools.offline_bundle build
python -m aerobim.tools.offline_bundle verify
python -m aerobim.tools.offline_bundle smoke
```

`smoke` path: `docker rmi` tag → `docker load` from tar → run container `--network none` → health + capabilities HTTP checks.

CI: `.github/workflows/ci.yml` job `offline-bundle-smoke` (on `main`).

## What is NOT VERIFIED

| Item | Status |
|---|---|
| Bare-metal wheelhouse install without Docker | NOT VERIFIED |
| Full npm cache offline frontend rebuild inside bundle | UNKNOWN / check current bundle manifest |
| Hugging Face / cloud LLM in offline mode | N/A — default deny; advisory optional |
| This session re-ran full Docker smoke | NOT_REPRODUCED_THIS_CYCLE (requires Docker time/disk) |

## Capabilities expected offline

Deterministic analyze path without external LLM/OCR extras may run with skipped/missing optional capabilities. Do not claim full feature parity offline without the smoke artifact for that build.

## Forbidden claims

«Работает в любом закрытом контуре без Docker» — запрещено до bare-metal evidence.
