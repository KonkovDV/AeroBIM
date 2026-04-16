# AeroBIM Standalone Runbook

## Purpose

This runbook describes the smallest sound way to operate AeroBIM as a standalone review stack: Python backend plus browser review shell.

## Runtime Topology

- `backend/` hosts the validation kernel and report/export APIs.
- `frontend/` hosts the browser review shell for report inspection, export actions, 3D IFC review, and 2D evidence overlays.
- persisted reports live under `AEROBIM_STORAGE_DIR/reports/*.json`.
- persisted drawing previews live under `AEROBIM_STORAGE_DIR/drawing-assets/<report_id>/`.

## Prerequisites

- Python 3.12+
- Node 20+
- on environments that need raster OCR: install the backend `vision` extra

## Local Bootstrap

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,vision]"
python -m aerobim.main
```

Expected health probe:

```bash
curl http://127.0.0.1:8080/health
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Default browser URL:

```text
http://127.0.0.1:5173
```

## Docker Bootstrap

The provided `docker-compose.yml` currently runs the backend slice and mounts report storage plus read-only samples.

```bash
docker compose up --build
```

Expected backend URL:

```text
http://127.0.0.1:8080
```

The frontend remains an independent static/browser shell in this tranche. Run it locally or deploy the generated `frontend/dist` bundle behind any static file host.

## Operational Sequence

Fastest deterministic path:

```bash
cd backend
python -m aerobim.tools.run_live_review_smoke
```

This one-command harness boots an isolated local stack, seeds the deterministic runtime review report, verifies core browser review state, and emits screenshot plus Playwright trace artifacts.

From the parent VS Code workspace, the same path is exposed as the `process: smoke:live-review` task.

1. start the backend;
2. validate `GET /health`;
3. submit a validation request or use fixture-driven report generation;
	for larger project packages, you can use `POST /v1/analyze/project-package/submit` and poll `GET /v1/analyze/project-package/jobs/{job_id}` until a `report_id` is present;
3a. if an OpenRebar reinforcement `*.result.json` is available, include `reinforcement_report_path` (and optionally `reinforcement_source_digest`) in the project-package payload to enable cross-document provenance warnings;
3b. if release policy requires a waste guardrail, also pass `reinforcement_waste_warning_threshold_percent` to flag high-waste reinforcement snapshots during review;
3c. if OpenRebar provenance drift must block release candidates, set `reinforcement_provenance_mode=enforced` to escalate those warnings into errors;
3d. if digest must be generated deterministically in AeroBIM, call `POST /v1/analyze/project-package/reinforcement-digest` with `reinforcement_report_path` and reuse returned `provenance_digest` as `reinforcement_source_digest`;
3d-alt. for shell-only/offline flow, compute the same value via `python -m aerobim.tools.openrebar_provenance_digest <openrebar.result.json>`;
3e. for a repeatable local throughput baseline, run `python -m aerobim.tools.benchmark_project_package --iterations 1 --warmup-iterations 0` and inspect the emitted JSON timing summary;
4. for deterministic runtime smoke, run `python -m aerobim.tools.seed_smoke_report` inside `backend/`;
5. confirm `GET /v1/reports` returns the seeded persisted report summary;
6. confirm `GET /v1/reports/{report_id}/source/ifc` returns the stored IFC source for that seeded report;
7. confirm `GET /v1/reports/{report_id}/drawing-assets/{asset_id}/preview` returns a stored drawing preview for that seeded report;
8. start the frontend shell and confirm it resolves the API base URL;
9. inspect issue provenance, 3D spatial selection, 2D overlay evidence, and HTML/JSON/BCF export buttons against the seeded runtime report.
10. if browser-level artifacts are needed, run `cd frontend && npm run smoke:browser` to capture live screenshots and a Playwright trace zip against the seeded report; if Vite starts on a fallback port, pass it explicitly with `--base-url`.

## Failure Modes

### Missing raster OCR dependency

Symptom: PDF works, raster image analysis raises a runtime dependency error.

Action:

```bash
cd backend
pip install -e ".[vision]"
```

### Empty report list in frontend

Symptom: frontend loads but shows no reports.

Checks:

- backend is reachable at the configured API base URL;
- `AEROBIM_STORAGE_DIR/reports` contains JSON files;
- `GET /v1/reports` returns `count > 0`.
- if the browser is running on `127.0.0.1:5173`, either keep backend debug defaults enabled or include that origin explicitly in `AEROBIM_CORS_ORIGINS`.

### Benchmark rail fails before producing JSON output

Symptom: `python -m aerobim.tools.benchmark_project_package` exits with a fixture-path or dependency error.

Checks:

- the referenced benchmark manifest exists under `samples/benchmarks/`;
- all fixture paths inside the manifest still resolve under `samples/`;
- the backend virtual environment includes the same extras needed by the selected pack.

### Export download returns 404

Symptom: HTML/JSON/BCF buttons fail for a selected report.

Checks:

- the selected `report_id` still exists under `storage_dir/reports`;
- the frontend API base URL points to the correct backend;
- the backend process has read access to the storage directory.

### Drawing preview overlay stays empty

Symptom: the issue has `problem_zone` data, but the 2D evidence panel has no sheet preview.

Checks:

- the selected report contains `drawing_assets` in `GET /v1/reports/{report_id}`;
- `GET /v1/reports/{report_id}/drawing-assets/{asset_id}/preview` returns `200`;
- the issue `sheet_id` and `page_number` match one persisted drawing asset.

### IFC viewer fails to load a model

Symptom: report data loads, but the viewer shows an IFC source or initialization error.

Checks:

- `GET /v1/reports/<report_id>/source/ifc` returns `200`;
- the stored IFC path still resolves within `AEROBIM_STORAGE_DIR`;
- the selected report was created through the current backend path rather than seeded from an external absolute location.