# Frontend review shell

[продукт (RU)](../README.md) · [Product README (EN)](../README.en.md)

The browser workplace is a **review shell over persisted reports**. It is not a CDE, not a model authoring tool, and not a replacement for the expert. The UI never writes `summary.passed` ([ADR-001](../docs/architecture/ADR-001-verdict-ownership-2026.md)). Checkpoint **`GO`**; `customer_go` false.

Sitting-member jury track remains the CLI (`python -m aerobim.tools.run_kt3_jury` from `backend/`). This shell is optional UI on the same clone.

## What you can open today

Eight information-architecture screens (`src/lib/tz-ui-screens.ts`). Every row is **`partial`**, not a delivered full-cycle workplace and not a closed Web-UI TZ matrix.

| Screen | What git actually does |
|---|---|
| Projects | Persisted report index; selecting a pack opens the expert three-pane |
| Upload | `POST /v1/uploads` dropzone, progress, cancel; RVT / NWD / DWG rejected before POST |
| Run | Analyze job with **polling** of `jobs/{job_id}` (SSE is not shipped); TZ 30:00 is a goal, not a measured SLA |
| Expert | Findings + 3D + remark on one screen (`data-testid="rehearsal-one-click"`). Sheet-error highlight is P1-smoke / pilot, not this pane |
| Remark | HITL edit → `POST .../review-events`; ITZ/STO/SP clause; storey/axis from the IFC index or an explicit “not in index” |
| Export | HTML, JSON, BCF 2.1/3.0; **PDF = coverage draft** (`GET .../export/pdf`). There is no XLSX endpoint |
| Diff | HTTP finding delta between two reports; `no_longer_reported` does not mean resolved |
| User | TZ coverage map + acceptance snapshot; default `GET /v1/auth/bff` = **501**. A lab `200 LAB` cookie is not customer SSO |

**One rehearsal click.** Development-only `POST /v1/demo/seed-fixture` (unpublished in OpenAPI; git walls + IDS, not a customer pack) or a finished analyze job lands on the expert three-pane with BCF on the same bar. The Export tab is not required for that landing.

Filter presets are **browser storage** or **JSON file exchange**. Legacy `team` scope is migrated to `file`. There is no team-sync server.

## Stack

Fact, not a roadmap: React 19, TypeScript, **Vite 7** SPA (not Next.js), Three.js, web-ifc (lazy chunk), vitest 4 + Testing Library. Playwright is only `smoke:browser` and `smoke:decision`. TanStack / Storybook / Tailwind are not in this tree.

Visible copy goes through `src/lib/i18n/ru.ts`. CDN fonts are not loaded.

Publishable frontend test counts are only in [`docs/evidence/runtime-baseline-latest.json`](../docs/evidence/runtime-baseline-latest.json) (`attested_by=ci`). A local `npm test` count is not that pin.

## Run

API default: `http://127.0.0.1:8080`. Vite is pinned to `http://127.0.0.1:5173` (`strictPort`; never Next.js `3000`). One command starts **API + Vite** (`npm ci` if Vite is missing). Node 20+ is required for this shell; the jury CLI is not.

```bash
python scripts/run_review_shell.py
```

Linux/macOS from the repo root: `./start.sh`. Windows PowerShell: `.\start.bat` (the `.\` is required). Do not type `start` (Start-Process) or `start.bat` without the prefix. Explorer: double-click `start.bat`. CMD: `start.bat`. If 8080 or 5173 is held by a leftover process, stop it and retry.

Same stand from `backend/` (venv active): `python -m aerobim.tools.run_review_stand`. From this directory: `npm start`. Ctrl+C stops both processes. Dedicated storage; click «Загрузить демонстрационный комплект». Not the jury CLI.

The API tree is `<clone>/backend`, not a `/tmp`-only copy of this UI. If the frontend was copied elsewhere, set `AEROBIM_BACKEND_DIR` to that `backend` directory and `AEROBIM_FRONTEND_DIR` to this tree. The combined launcher runs `backend/.venv/Scripts/python.exe -m aerobim.main` on Windows and `backend/.venv/bin/python -m aerobim.main` on Linux.

Vite only (smokes, already-running API):

```bash
npm ci
npm run lint
npm test
npm run dev
```

Override the API:

```bash
VITE_AEROBIM_API_BASE_URL=http://127.0.0.1:8080
```

If 5173 is busy, stop the leftover Vite process. Combined live smoke from `backend/` may use 5174 or 4173; it never binds Next.js port 3000:

```bash
python -m aerobim.tools.run_live_review_smoke
```

Browser capture (backend running, one smoke report seeded, Vite at `http://127.0.0.1:5173`):

```bash
npm run smoke:browser
```

The script checks live export links, overlay presence, preset JSON-file exchange (not team), and clash-focus, then writes under `frontend/artifacts/` (gitignored):

- `artifacts/browser-smoke/review-shell-issue.png`
- `artifacts/browser-smoke/review-shell-clash.png`
- `artifacts/browser-smoke/review-shell-smoke.trace.zip`

If the combined smoke moved Vite to `5174`: `npm run smoke:browser -- --base-url http://127.0.0.1:5174`.

Decision half of the same rehearsal — remark card to `accepted`, the
draft-vs-confirmed JSON pair, loopback-only traffic, 1366×768 / 1280×800 and the
print stylesheet:

```bash
npm run smoke:decision
```

It needs a freshly seeded report: a finding that already carries a decision is
not editable, and the script says so instead of hanging. Re-running
`python -m aerobim.tools.seed_smoke_report` (or `run_live_review_smoke`) wipes
the HITL journal for that report so the rehearsal is repeatable. Artifacts
land next to the ones above, also gitignored.

Playwright Chromium belongs in the default user cache
(`%LOCALAPPDATA%\ms-playwright` on Windows). `npx playwright install chromium`
from `frontend/`. Do not pin `PLAYWRIGHT_BROWSERS_PATH` at an ephemeral
TEMP directory — that path disappears, and `run_live_review_smoke` already
drops the inherited variable.

## Honesty limits

- WASM IFC viewer cap **256 MiB**. Disk analyze on a hard profile up to **1.5 GB** is RocksDB on the backend, not this viewer.
- Federated ~1 GB models are not loaded into the browser.
- Outbound advisory LLM/VLM never flips `summary.passed`.
- Lab HITL: expert/reviewer write; `user`/`viewer` → 403.
- Authoring-tool roundtrip (write back to Revit/Navisworks) is not implemented.

Claim boundary: [`docs/pilot-claim-boundary-2026.md`](../docs/pilot-claim-boundary-2026.md).
