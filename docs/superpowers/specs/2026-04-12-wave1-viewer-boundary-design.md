# AeroBIM Wave 1 Viewer Boundary Design

## Goal

Add the first spatial review tranche without changing the persisted report model or turning the frontend into a second source of validation truth.

## Decision

Adopt raw `web-ifc + Three.js` for the first viewer boundary.

## Why This Path

- local repo docs already select `web-ifc + Three.js` as the preferred viewer rail;
- `web-ifc` remains the canonical browser IFC substrate and exposes direct `GetExpressIdFromGuid()` lookup, which makes issue-to-element navigation straightforward;
- this path avoids AGPL viewer risk from xeokit while keeping a future higher-level viewer option open.

## Backend Contract

The browser must not read `ifc_path` directly from persisted report JSON.

Instead, the frontend uses a report-scoped backend endpoint:

- `GET /v1/reports/{report_id}/source/ifc`

Boundary rules:

- report ID remains the public handle;
- IFC file access stays server-side;
- path resolution stays constrained to the configured storage boundary.

## Frontend Shape

1. Keep the existing report list, issue detail, and provenance shell.
2. Add a dedicated viewer panel downstream of the selected report.
3. Load IFC bytes only through the new report-scoped endpoint.
4. Build the scene from `IfcAPI.OpenModel()` plus streamed geometry.
5. Use `GetExpressIdFromGuid()` to map `ValidationIssue.element_guid` to scene selection.
6. Support two first-order review interactions:
   - highlight selected issue element;
   - isolate selected issue element.

## Explicit Deferrals

- no 2D problem-zone overlay rendering in this tranche;
- no clash-pair dual selection UX yet;
- no higher-level viewer abstraction layer;
- no frontend testing framework expansion unless the current tranche proves insufficiently verifiable through build + smoke.

## Verification Plan

- backend HTTP endpoint tests stay green;
- frontend dependencies install cleanly;
- frontend build passes with `web-ifc` and `three` integrated;
- docs and smoke notes are updated to mention the IFC source endpoint and viewer rail.