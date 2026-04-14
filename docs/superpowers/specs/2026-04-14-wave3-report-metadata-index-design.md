# AeroBIM Wave 3 Report Metadata Index Design

## Goal

Make persisted reports operationally sortable and filterable by adding lightweight project metadata to the report contract and exposing query semantics on the report index.

## Problem

Persisted reports currently expose only `report_id`, `request_id`, timestamp, pass/fail, and issue count.

That is enough for ad hoc debugging, but not for project-level operational use. Operators cannot distinguish reports by project or discipline without opening each report individually.

## Decision

Add flattened metadata fields to the report/request contracts and support index-level filtering on `/v1/reports`.

Chosen minimal fields:

- `project_name`
- `discipline`

Chosen minimal filters:

- `project`
- `discipline`
- `passed`

## Contract Shape

Add the same two metadata fields to:

- `ValidationRequest`
- `ValidationReport`
- `ReportSummaryEntry`

This keeps the index payload self-sufficient and avoids forcing the frontend to fetch every full report just to render project-level context.

## API Semantics

`GET /v1/reports` remains the index endpoint, but now accepts optional query params:

- `project=<substring>`
- `discipline=<substring>`
- `passed=true|false`

Matching rules:

- `project` and `discipline` are case-insensitive substring filters;
- `passed` is an exact boolean filter;
- filters compose with logical `AND`.

## Persistence Strategy

Metadata persists in the canonical report JSON next to existing top-level report fields.

No new storage directories or side indexes are introduced in this tranche. `FilesystemAuditStore.list_reports()` continues scanning report JSON files, but now reconstructs and returns metadata-bearing summaries.

## Frontend Scope

The frontend report index should:

1. display `project_name` and `discipline` on report cards when present;
2. include those fields in the existing client-side search;
3. remain compatible with older reports that do not contain metadata.

## Explicit Deferrals

- no nested metadata object or taxonomy system;
- no multi-select discipline tagging;
- no server-side pagination yet;
- no dedicated filter controls beyond the existing search box in this tranche.

## Verification Plan

- backend store tests for metadata roundtrip and summary listing;
- API tests for `/v1/reports` filter semantics;
- targeted use-case/API regression for metadata propagation;
- frontend build or targeted tests if the report index UI changes;
- docs sync for Wave 3 and the live smoke seed path.