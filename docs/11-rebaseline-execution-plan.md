---
title: "AeroBIM Rebaseline Execution Plan"
status: active
version: "0.2.0"
last_updated: "2026-04-12"
tags: [aerobim, plan, how-to]
---

# AeroBIM Rebaseline Execution Plan

## Goal

Turn the current validation kernel into an operator-usable review product without breaking the stable backend contracts already present in the repository.

## Current Baseline

- backend validation kernel is live;
- persisted report model and JSON / HTML / BCF exports are live;
- initial browser spatial review shell is live;
- Revit boundary remains docs-first;
- spatial review and operating-model maturity remain the main gaps.

## Wave 0 — Baseline Truth And Reliability

### Status

Launched on 2026-04-12.

Initial tranche completed in the same session:

- docs rebaseline finished;
- clash temp-directory cleanup hardening landed;
- targeted backend tests passed;
- frontend build passed;
- workspace docs closure rail passed.

### Scope

- refresh the academic audit and execution plan;
- sync stale docs to the current runtime state;
- fix confirmed low-risk reliability defects discovered during rebaseline;
- clarify optional capability gating for operators.

### Tranche Started In This Session

1. repo-grounded audit and recommendations;
2. stale-doc sync for frontend, ops, and runtime interpretation;
3. `IfcClashDetector` temp-directory cleanup hardening;
4. optional extra visibility improvements for `.[clash]` and `.[docling]`.

### Verification

- targeted backend tests for clash/export path;
- frontend build;
- docs closure rail.

## Wave 1 — Spatial Review Surface

### Status

Launched on 2026-04-12.

Initial tranche completed in the same session:

- backend report-scoped IFC source endpoint landed;
- endpoint tests for source-path safety and availability passed;
- frontend `web-ifc + Three.js` viewer rail landed;
- issue-to-element highlight / isolate flow landed;
- clash-pair focus and generic multi-selection isolate flow landed;
- drawing asset/page switching landed in the 2D evidence rail;
- App-level smoke regression now covers report -> issue/clash -> viewer -> 2D overlay -> provenance -> export over mocked persisted report data;
- deterministic live smoke seeding now materializes one persisted runtime report for backend/frontend manual verification;
- viewer runtime is lazy-loaded to avoid inflating the initial report-shell bundle.

### Goal

Move the frontend from report browser to engineering review surface.

### Deliverables

1. `web-ifc + Three.js` viewer rail. ✅ initial tranche complete
2. issue selection -> IFC GUID highlight / isolate flow. ✅ initial tranche complete
3. 2D `ProblemZone` rendering for PDF/image evidence.
4. persisted-report smoke path for full UI inspection.

### Exit Criteria

- a reviewer can click an issue and land on the corresponding element or 2D evidence region;
- the viewer remains downstream of the report model, not a competing source of truth.

## Wave 2 — Multimodal Hardening

### Goal

Increase evidence quality without replacing typed contracts.

### Deliverables

1. integration tests for real `ifcclash` geometry runs when the extra is installed. Coverage rail landed and first runtime proof is captured in an extra-enabled environment.
2. integration tests for Docling-backed non-text requirement extraction. Coverage rail landed and first runtime proof is captured in an extra-enabled environment.
3. optional heavier vision/VLM adapter behind the existing `VisionDrawingAnalyzer` port;
4. confidence/calibration rules for mixed drawing evidence sources.

### Exit Criteria

- optional adapters are testable and operationally explicit;
- stronger multimodal extraction does not alter downstream contracts.

## Wave 3 — Operational Scale

### Status

Started on 2026-04-14.

Initial tranche completed in the same session:

- persisted reports now carry `project_name` and `discipline` metadata;
- `/v1/reports` now supports queryable `project`, `discipline`, and `passed` filters;
- the frontend report index now displays project/disciplines metadata and includes those fields in the existing search flow.

Second tranche completed in the same session:

- `POST /v1/analyze/project-package/submit` now accepts same-process background jobs for larger packages;
- `GET /v1/analyze/project-package/jobs/{job_id}` now exposes async status polling with `queued/running/succeeded/failed` states;
- the first Wave 3 async runner stays intentionally in-memory and same-process, without introducing an external queue.

Third tranche completed in the same session:

- `samples/benchmarks/project-package-baseline.json` now defines a representative benchmark pack for multimodal project-package validation;
- `python -m aerobim.tools.benchmark_project_package` now executes the real `AnalyzeProjectPackageUseCase` over that pack and emits JSON timings plus throughput summary;
- the first fixture-backed benchmark proof is now captured locally against the baseline pack.

Fourth tranche completed in the same session:

- the frontend report index now exposes explicit `project`, `discipline`, and pass/fail controls instead of keeping those semantics backend-only;
- `frontend/src/lib/api.ts` now forwards report filter query params to `/v1/reports`;
- the report shell keeps local text search, but only within the already server-filtered result set.

Fifth tranche completed in the same session:

- `samples/benchmarks/project-package-fire-compliance.json` now provides a second throughput profile instead of anchoring the benchmark rail to one pack only;
- benchmark regression tests now assert that both canonical benchmark manifests load against real repository fixtures;
- the second pack has a local runtime proof via `python -m aerobim.tools.benchmark_project_package --pack ../samples/benchmarks/project-package-fire-compliance.json`.

### Goal

Make reports operationally manageable, not just persistable.

### Deliverables

1. project/disciplines metadata on report storage;
2. queryable report index and filter semantics;
3. async job execution for larger packages;
4. benchmark pack and throughput rail.

### Exit Criteria

- large or repeated validations do not depend on ad hoc local execution habits;
- report retrieval works at project scope, not only by raw `report_id`.

## Wave 4 — Thin Authoring Roundtrip

### Goal

Add a thin Revit-side client only after the server-side kernel and review surface are stable.

### Deliverables

1. issue fetch and focus contract;
2. comment/status pushback contract;
3. packaging and deployment notes.

### Exit Criteria

- the plugin remains a thin synchronization surface, not a second validation kernel.

## What Not To Do Yet

- do not introduce event sourcing or agentic runtime orchestration;
- do not make the Revit plugin fat;
- do not adopt AGPL viewer/runtime dependencies by default without an explicit licensing decision;
- do not turn SHACL into the primary MVP validation surface.

## Recommended Next Concrete Tranche

1. add at least one genuinely larger stress-oriented benchmark pack so the throughput rail spans both profile diversity and model size;
2. promote benchmark and live-smoke rails from local runtime proofs into a repeatable CI or release-readiness stage when the stack bootstrap becomes stable enough;
3. consider richer operator workflows on top of the new frontend filters, such as saved filter presets or report-group views, only if real review volume justifies them.