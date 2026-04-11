---
title: "Samolet Strategy And Delivery Plan"
status: active
version: "0.2.0"
last_updated: "2026-04-08"
tags: [samolet, strategy, explanation]
---

# Samolet Strategy And Delivery Plan

## Goal

Build an isolated product that turns project requirements, drawings, calculations, IDS packages, and model-delivery expectations into an operational multimodal BIM quality workflow.

## Product Boundary

### In Scope

- requirements ingestion from structured text, narrative TZ/calculation text, IDS, and later rich document packages;
- IFC validation kernel with quantity and property checks;
- 2D drawing annotation ingestion and cross-check against normalized rules;
- generated remarks for designers with explicit provenance;
- issue generation and audit persistence;
- machine-readable outputs (`json`, `html`, `bcf` later);
- review UI and thin Revit-side workflow;
- openBIM-first interoperability.

### Out Of Scope For MVP

- full digital twin platform;
- autonomous multi-agent orchestration;
- generic plugin marketplace;
- enterprise data lake / knowledge graph;
- full construction ERP scope.

## What Must Be True

For the first meaningful product milestone to be considered successful, the following must be true:

1. A user can provide an IFC file and a requirement package.
2. The system can normalize those requirements into explicit machine-checkable rules.
3. The system can ingest drawing annotations or future CV output as structured evidence.
4. The validation kernel can produce deterministic findings tied to IFC entities, drawing zones, and source text.
5. Findings can be stored, replayed, and exported without losing provenance.
6. Reviewers can understand which requirement failed, where it failed, and what evidence supports the failure.
7. The architecture remains modular enough to swap viewers, validators, storage, and authoring-side clients without collapsing the core.

## Architectural Direction

`Samolet` keeps the MicroPhoenix architectural spine and removes the surrounding platform complexity.

### Canonical Layers

1. `core`
   shared primitives: container, tokens, config, result semantics, logging contracts.
2. `domain`
   pure BIM QA concepts: requirements, findings, reports, issue severity, invariants.
3. `application`
   use cases and workflow orchestration.
4. `infrastructure`
   adapters for IfcOpenShell, IfcTester, Docling, storage, export, external APIs.
5. `presentation`
   HTTP API, later web UI and plugin-facing transport surfaces.

### Non-Negotiable Invariants

- domain must not import infrastructure;
- all external libraries are hidden behind ports/adapters;
- composition happens in bootstrap only;
- request IDs and audit provenance are explicit;
- every new domain port ships with an adapter or remains intentionally unintroduced.

## Delivery Phases

## Phase 0: Foundation And Evidence Lock

### Deliverables

- isolated repo and project structure;
- extracted architecture dossier;
- openBIM / OSS / competitor / protocol landscape;
- atomic backlog.

### Exit Criteria

- repo is independent from `c:\plans` root git;
- architecture choices are explicit;
- first build path is clear.

## Phase 1: Requirement Normalization Kernel

### Deliverables

- structured requirement DSL;
- IDS package ingestion path;
- document-to-rule path for narrative specs;
- narrative rule-synthesis baseline for TZ and calculations;
- traceable requirement identifiers.

### Acceptance Criteria

- a requirement source produces deterministic normalized rule objects;
- each rule has provenance (`source`, `rule_id`, `entity`, `property`, `expected_value`).

## Phase 2: IFC Validation Core

### Deliverables

- IfcOpenShell-based model load and traversal;
- IfcTester-based IDS validation path;
- rule-to-entity/property/quantity evaluation;
- drawing-annotation cross-check baseline;
- issue severity mapping.

### Acceptance Criteria

- validator can distinguish: missing entity, missing property, wrong value, unsupported rule;
- findings are stable for repeated runs on the same inputs.

## Phase 3: Audit And Output Layer

### Deliverables

- report store;
- JSON and HTML export;
- BCF export path for coordination workflows;
- structured remark generation;
- issue grouping and deduplication.

### Acceptance Criteria

- each report includes request ID, source provenance, summary counts, and detailed evidence;
- BCF-ready topics carry IFC GUID and viewpoint metadata when available.

## Phase 4: Review Surfaces

### Deliverables

- browser review UI;
- model/object issue lookup;
- requirement-to-finding navigation;
- reviewer resolution workflow.

### Acceptance Criteria

- reviewer can open a report, inspect issues, filter by severity / discipline / requirement group, and export results.

## Phase 5: Authoring-Side Roundtrip

### Deliverables

- thin Revit-side client;
- import issues into authoring workflow;
- push statuses or comments back to review backend.

### Acceptance Criteria

- authoring-side user can pull assigned findings and return updated resolution state.

## Phase 6: Interoperability And Scale

### Deliverables

- BCF API / openCDE alignment;
- Documents API alignment;
- storage hardening and long-running job execution;
- tenant/project isolation.

### Acceptance Criteria

- the platform can plug into external CDE-style ecosystems without rewriting core domain logic.

## Technical Decisions

## Backend

Python is the primary backend language because the strongest open-source IFC and document-processing tools are Python-first.

### Why

- `IfcOpenShell` and `IfcTester` are first-class Python surfaces;
- `Docling` is Python-native;
- rule normalization, report generation, and orchestration are straightforward in Python;
- browser and plugin surfaces can remain independent bounded contexts.

## Frontend

Web review will be TypeScript-first.

### Why

- `web-ifc` and browser viewers are JavaScript-native;
- issue review and model navigation fit a browser surface better than a desktop-only path.

## Authoring Client

Revit integration stays thin.

### Why

- the product core must stay outside Revit;
- plugin should be a sync/orchestration client, not the canonical domain runtime.

## Major Risks

## Risk 1: Over-Copying MicroPhoenix

### Failure Mode

The team copies platform subsystems that do not produce BIM value.

### Mitigation

Keep only the architecture spine, not the platform estate.

## Risk 2: Premature Natural-Language Intelligence

### Failure Mode

The system attempts full free-text interpretation too early and produces low-trust rule extraction.

### Mitigation

Use a strict intermediate representation first; add richer semantic extraction only after provenance is stable.

## Risk 5: Fake Multimodality

### Failure Mode

The product claims AI/CV support but only hides brittle ad hoc parsing or silent placeholders.

### Mitigation

Keep AI and CV behind explicit adapters, preserve provenance, and label limited baselines honestly until real model-backed adapters land.

## Risk 3: Viewer-Led Architecture

### Failure Mode

The web viewer drives the domain model instead of consuming it.

### Mitigation

Keep viewer state in presentation; domain owns rules, findings, and reports.

## Risk 4: Revit-Centric Lock-In

### Failure Mode

The plugin becomes the system center and blocks openBIM interoperability.

### Mitigation

Keep Revit as one client among several, not the core.

## Verification Strategy

### Structural Verification

- unit tests for DI and use-case orchestration;
- contract tests for adapters;
- report snapshot tests;
- sample IFC + IDS regression pack;
- sample drawing/specification/calculation fixtures for multimodal regression.

### Goal-Backward Verification

Every milestone closes by verifying:

1. required artifacts exist;
2. they contain substantive logic;
3. they are wired into bootstrap and reachable from the runtime path.

## Immediate Next Build Target

The first concrete build target is narrow by design:

- ingest structured requirements plus one narrative spec/calculation source;
- ingest one structured drawing annotation pack;
- validate one IFC file against normalized rules;
- generate persisted findings and human-readable remarks through one HTTP endpoint.

That target is small enough to ship quickly and large enough to prove the multimodal architecture pivot.
