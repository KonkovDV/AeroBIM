# Frontend review shell

[Product README (EN)](../README.md) · [продукт (RU)](../README.ru.md)

The browser workplace is a **review shell over persisted reports**. It is not a CDE, not a model authoring tool, and not a replacement for the expert. The UI never writes `summary.passed` ([ADR-001](../docs/architecture/ADR-001-verdict-ownership-2026.md)). Checkpoint **`GO`**; `customer_go` false.

Sitting-member jury track remains the CLI (`python -m aerobim.tools.run_kt3_jury` from `backend/`). This shell is the IT-mentor laptop track.

## What you can open today

Eight information-architecture screens (`src/lib/tz-ui-screens.ts`). Every row is **`partial`**, not a delivered full-cycle workplace and not a closed Web-UI TZ matrix.

| Screen | What git actually does |
|---|---|
| Projects | Persisted report index; selecting a pack opens the expert three-pane |
| Upload | `POST /v1/uploads` dropzone, progress, cancel; RVT / NWD / DWG rejected before POST |
| Run | Analyze job with **polling** of `jobs/{job_id}` (SSE is not shipped); TZ 30:00 is a goal, not a measured SLA |
| Expert | Findings, sheet overlay + 3D, remark on one screen (`data-testid="rehearsal-one-click"`) |
| Remark | HITL edit → `POST .../review-events`; ITZ/STO/SP clause; storey/axis from the IFC index or an explicit “not in index” |
| Export | HTML, JSON, BCF 2.1/3.0; **PDF = coverage draft** (`GET .../export/pdf`). There is no XLSX endpoint |
| Diff | HTTP finding delta between two reports; `no_longer_reported` does not mean resolved |
| User | TZ coverage map + acceptance snapshot; default `GET /v1/auth/bff` = **501**. A lab `200 LAB` cookie is not customer SSO |

**One rehearsal click.** Development-only `POST /v1/demo/seed-fixture` (unpublished in OpenAPI; git walls + IDS, not a customer pack) or a finished analyze job lands on the expert three-pane with BCF on the same bar. The Export tab is not required for that landing.

Filter presets are **browser storage** or **JSON file exchange**. Legacy `team` scope is migrated to `file`. There is no team-sync server.

## Stack

Fact, not a roadmap: React 19, TypeScript, Vite 7, Three.js, web-ifc (lazy chunk), vitest 4 + Testing Library. Playwright is only `smoke:browser`. TanStack / Storybook / Tailwind are not in this tree.

Visible copy goes through `src/lib/i18n/ru.ts`. CDN fonts are not loaded.

Publishable frontend test counts are only in [`docs/evidence/runtime-baseline-latest.json`](../docs/evidence/runtime-baseline-latest.json) (`attested_by=ci`). A local `npm test` count is not that pin.

## Run

API default: `http://127.0.0.1:8080`.

```bash
cd frontend
npm ci
npm run lint
npm test
npm run dev
```

Override the API:

```bash
VITE_AEROBIM_API_BASE_URL=http://127.0.0.1:8080
```

Backend must be up (`python -m aerobim.main` from `backend/`). Combined live smoke from `backend/`:

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

If Vite moved off `5173`: `npm run smoke:browser -- --base-url http://127.0.0.1:3001`.

## Honesty limits

- WASM IFC viewer cap **256 MiB**. Disk analyze on a hard profile up to **1.5 GB** is RocksDB on the backend, not this viewer.
- Federated ~1 GB models are not loaded into the browser.
- Outbound advisory LLM/VLM never flips `summary.passed`.
- Lab HITL: expert/reviewer write; `user`/`viewer` → 403.
- Authoring-tool roundtrip (write back to Revit/Navisworks) is not implemented.

Plan for the executor: [`docs/quality/FRONTEND_DEVELOPMENT_PLAN_2026_09.md`](../docs/quality/FRONTEND_DEVELOPMENT_PLAN_2026_09.md). Claim boundary: [`docs/pilot-claim-boundary-2026.md`](../docs/pilot-claim-boundary-2026.md).
