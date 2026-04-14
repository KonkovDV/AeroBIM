# AeroBIM Wave 3 Benchmark Throughput Rail Design

## Goal

Add a repeatable benchmark rail for `analyze/project-package` so future throughput claims are grounded in representative fixture packs instead of ad hoc timing runs.

## Problem

`AeroBIM` now has persisted reports, report indexing, async submit/status, and live review smoke, but it still lacks a first-class benchmark path for larger project-package validation.

Without that rail, any latency or throughput claim remains anecdotal.

## Decision

Introduce a manifest-backed benchmark pack plus a small CLI runner under `backend/src/aerobim/tools/`.

The runner will:

1. load a benchmark-pack manifest from `samples/benchmarks/`;
2. resolve fixture paths relative to the repo root;
3. bootstrap the real `AnalyzeProjectPackageUseCase`;
4. execute warmup iterations plus measured iterations;
5. emit JSON with per-iteration timings and aggregate summary metrics.

## Pack Shape

Each pack manifest contains:

- `pack_id`
- `description`
- `project_name`
- `discipline`
- request inputs:
  - `ifc_path`
  - `requirement_path`
  - optional `ids_path`
  - optional `technical_spec_path`
  - optional `calculation_path`
  - optional `drawings[]`

## Output Shape

The runner emits JSON with:

- `pack_id`
- `iterations`
- `warmup_iterations`
- `measured_runs[]` with `elapsed_ms`, `report_id`, and issue/requirement counts
- `summary` with `min_ms`, `max_ms`, `avg_ms`, and `reports_per_second`

## Scope Boundaries

- no new async executor or queue surface;
- no CI performance budget enforcement yet;
- no historical benchmark database;
- no frontend surface for benchmark results in this tranche.

## Verification Plan

- pure helper tests for manifest loading and aggregate timing summary;
- one real CLI run against the baseline benchmark pack;
- docs sync for the new benchmark rail and Wave 3 progress.