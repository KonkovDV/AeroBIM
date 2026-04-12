# AeroBIM Wave 1 Drawing Overlay Contract Design

## Goal

Add real 2D `ProblemZone` overlays without leaking raw local file paths into the browser and without turning the frontend into a second source of evidence truth.

## Problem

`ProblemZone` already exists in persisted findings, but the report model does not persist any drawing asset that the frontend can render underneath those coordinates.

As a result, a browser overlay cannot be implemented honestly from the current report contract alone.

## Decision

Introduce a report-scoped `drawing_assets` contract in `ValidationReport` and a report-scoped preview endpoint.

## Contract Shape

Each persisted report may include zero or more drawing assets.

Minimum fields:

- `asset_id`
- `sheet_id`
- `page_number`
- `media_type`
- `coordinate_width`
- `coordinate_height`

Interpretation:

- `coordinate_width` and `coordinate_height` define the coordinate space used by `ProblemZone` for the corresponding sheet/page;
- the frontend scales overlays relative to this coordinate space instead of assuming pixel-equal coordinates.

## Persistence Strategy

The browser must never read original drawing file paths from report JSON.

Instead:

1. `AnalyzeProjectPackageUseCase` materializes logical drawing assets from `DrawingSource` inputs.
2. `FilesystemAuditStore.save()` persists preview PNGs under the storage boundary.
3. The store rewrites each asset into a report-safe persisted form backed by an internal relative preview path.

Storage layout:

- `${AEROBIM_STORAGE_DIR}/drawing-assets/<report_id>/<asset_id>.png`

## Backend Endpoint

Add a report-scoped endpoint:

- `GET /v1/reports/{report_id}/drawing-assets/{asset_id}/preview`

Boundary rules:

- `report_id` remains the public handle;
- `asset_id` is scoped to the report;
- preview path resolution must stay inside the configured storage boundary;
- missing or out-of-bound assets return safe `404` / `409` semantics.

## Preview Generation Rules

- Raster image inputs (`png`, `jpg`, `jpeg`, `webp`) are normalized into PNG previews.
- PDF inputs generate one PNG preview per page via PyMuPDF.
- Structured text-only drawing inputs produce no drawing asset.

## Frontend Shape

1. Keep the existing report shell and 3D viewer intact.
2. Add a 2D evidence panel that activates only when the active issue has `problem_zone` and a matching persisted drawing asset.
3. Load preview bytes only through the new report-scoped endpoint.
4. Render the preview image plus an absolutely positioned overlay rectangle scaled from `ProblemZone` coordinates.

## Explicit Deferrals

- no annotation editing;
- no multi-page gallery beyond the asset matched to the active issue;
- no PDF text layer rendering;
- no drawing asset generation for structured text annotations without file-backed source media.

## Verification Plan

- backend tests for drawing asset persistence and preview endpoint safety;
- use-case test that PDF/image drawing sources materialize drawing assets;
- frontend build passes with the new overlay panel;
- docs and smoke path mention issue-driven 2D evidence overlays.