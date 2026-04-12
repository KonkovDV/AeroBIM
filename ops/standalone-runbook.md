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

1. start the backend;
2. validate `GET /health`;
3. submit a validation request or use fixture-driven report generation;
4. confirm `GET /v1/reports` returns persisted report summaries;
5. confirm `GET /v1/reports/{report_id}/source/ifc` returns the stored IFC source for one persisted report;
6. confirm `GET /v1/reports/{report_id}/drawing-assets/{asset_id}/preview` returns a stored drawing preview for one persisted report;
7. start the frontend shell and confirm it resolves the API base URL;
8. inspect issue provenance, 3D spatial selection, 2D overlay evidence, and HTML/JSON/BCF export buttons.

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