# AeroBIM Wave 3 Frontend Report Filters Design

## Goal

Expose the existing backend report-index filters as explicit operator controls in the browser review shell instead of leaving them as backend-only query semantics.

## Problem

`/v1/reports` already supports `project`, `discipline`, and `passed`, but the frontend still loads the full list and only performs client-side text search.

That keeps Wave 3 technically complete on the API side, but not operationally complete for the actual review workflow.

## Decision

Add a small filter bar to the report index and extend `fetchReports()` to send query params.

Controls:

- `Project` text input → backend `project`
- `Discipline` text input → backend `discipline`
- `Status` select → backend `passed`
- keep the existing local text search, but narrow its purpose to report/request IDs within the already filtered result set

## UX Rules

- backend filters are debounced through `useDeferredValue()`;
- if the currently selected report disappears from the filtered result set, select the first remaining report or clear selection;
- local search stays purely client-side and does not replace backend filtering.

## Scope Boundaries

- no saved filter presets;
- no pagination;
- no server-driven facet values;
- no rewrite of the report detail or viewer surfaces.

## Verification Plan

- frontend unit tests for query-param forwarding and filtered selection behavior;
- `npm test` for the frontend suite;
- `npm run build` for the frontend shell;
- active docs sync if the standalone workflow description changes.