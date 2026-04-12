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

1. integration tests for real `ifcclash` geometry runs when the extra is installed;
2. integration tests for Docling-backed non-text requirement extraction;
3. optional heavier vision/VLM adapter behind the existing `VisionDrawingAnalyzer` port;
4. confidence/calibration rules for mixed drawing evidence sources.

### Exit Criteria

- optional adapters are testable and operationally explicit;
- stronger multimodal extraction does not alter downstream contracts.

## Wave 3 — Operational Scale

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

1. add 2D evidence overlay rendering for drawing problem zones;
2. add a frontend smoke path that proves report -> issue/clash -> viewer -> provenance -> export against one persisted report;
3. design and land a persisted drawing-asset contract so 2D problem-zone overlays can be real rather than synthetic.