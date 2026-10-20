# Frontend review shell

[Product README (EN)](../README.md) · [продукт (RU)](../README.ru.md)

The browser is the expert's table: the model, the sheet, the finding, and a hand on the remark ([ADR-001](../docs/architecture/ADR-001-verdict-ownership-2026.md)).

The command-line check (`python -m aerobim.tools.run_kt3_jury` from `backend/`) runs without a browser. This shell is the same clone, with the light on.

## What you can open today

Eight screens (`src/lib/tz-ui-screens.ts`). Each one already does its piece of the review.

| Screen | On screen |
|---|---|
| Projects | The pack list; one click opens the three panes |
| Upload | Dropzone, progress, cancel. IFC and PDF come in; RVT, NWD and DWG turn back before the upload |
| Run | The job, alive by polling `jobs/{job_id}` |
| Expert | Findings, the model and the remark on one screen |
| Remark | The expert's edit, the clause, the storey, straight into `review-events` |
| Export | HTML, JSON, BCF 2.1/3.0, and a PDF draft |
| Diff | The delta of findings between two reports |
| User | The coverage map and the acceptance snapshot |

**One rehearsal click.** In a Vite dev build, `POST /v1/demo/seed-fixture` or a finished analyze job lands on the expert's three panes, with BCF on the same bar.

Filter presets live in the browser or travel as a JSON file.

## Stack

React 19, TypeScript, **Vite 8**, Three.js, web-ifc, Vitest 5. Playwright drives `smoke:browser`, `smoke:decision` and `smoke:demo`.

Visible copy goes through `src/lib/i18n/ru.ts`.

The test counts worth citing live in [`docs/evidence/runtime-baseline-latest.json`](../docs/evidence/runtime-baseline-latest.json) (`attested_by=ci`).

## Run

API at `http://127.0.0.1:8080`. Vite at `http://127.0.0.1:5173`. One command starts **API + Vite** (`npm ci` if Vite is missing). Node 22.22.2+ carries this shell (`engines` + `engine-strict` in `.npmrc`).

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

The seed button has its own rehearsal. In a Vite dev build, `npm run smoke:demo`
presses «Загрузить демонстрационный комплект» and follows
`POST /v1/demo/seed-fixture` to the expert's panes.

Playwright Chromium belongs in the default user cache
(`%LOCALAPPDATA%\ms-playwright` on Windows). `npx playwright install chromium`
from `frontend/`. Do not pin `PLAYWRIGHT_BROWSERS_PATH` at an ephemeral
TEMP directory — that path disappears, and `run_live_review_smoke` already
drops the inherited variable.

## Scale

- The browser holds **256 MiB** of IFC. The worker on disk goes to **1.5 GB** through RocksDB.
- The verdict stays with the program.
- Expert and reviewer write the decision.

Map of the claims: [`docs/pilot-claim-boundary-2026.md`](../docs/pilot-claim-boundary-2026.md).
