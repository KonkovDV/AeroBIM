---
title: "Samolet Architecture Reference"
status: active
version: "0.3.0"
last_updated: "2026-04-08"
tags: [samolet, architecture, reference]
---

# Samolet Architecture Reference

## Purpose

This document is the canonical architecture reference for `Samolet` at the current phase. It converts the strategy, landscape research, and corrected fact-check audit into one implementation-oriented source of truth.

## Product Definition

`Samolet` is an intelligent documentation and BIM quality kernel for construction projects.

The product is meant to:

1. ingest and cross-reference project documentation, working documentation, technical specifications, and calculation materials;
2. ingest and validate IFC deliverables and IDS packages;
3. analyze 2D drawings and BIM models for dimensional, spatial, and property compliance;
4. detect collisions, inconsistencies, and errors in dimensions and areas;
5. find discrepancies between documents, technical specifications, calculations, and adjacent disciplines;
6. normalize findings into machine-checkable rules with explicit provenance;
7. persist findings with provenance and spatial context;
8. highlight problem zones and generate structured remarks for designers;
9. export issue packs for review and coordination;
10. support browser review and thin authoring-side roundtrip later.

## What The Product Is Not

- not a full CDE;
- not a general-purpose BIM authoring tool;
- not a Revit-centered runtime;
- not a semantic-web platform first;
- not a replacement for Solibri or Navisworks on day one.

## Canonical Standards Stack

### IFC

Use IFC as the primary model-exchange substrate. Anchor semantics to ISO 16739-1:2024.

### IDS

Use IDS 1.0 as the primary portable rule-expression surface for deliverable requirements.

### BCF

Use BCF as the issue transport layer for findings, viewpoints, and coordination handoff.

### bSDD

Use bSDD only as a terminology enrichment and mapping service.

### SHACL

Treat SHACL as an optional semantic extension layer for RDF-backed knowledge graphs or validation overlays. Do not make it the MVP rule language.

## Layer Model

`Samolet` keeps the extracted MicroPhoenix spine:

1. `core`
2. `domain`
3. `application`
4. `infrastructure`
5. `presentation`

### Core

Owns container, tokens, config primitives, and cross-cutting runtime contracts.

### Domain

Owns requirements, findings, reports, severities, invariants, and domain ports.

### Application

Owns use cases and workflow orchestration.

### Infrastructure

Owns adapters for IfcOpenShell, IfcTester, Docling, persistence, exports, viewers, and enterprise APIs.

### Presentation

Owns HTTP, browser-facing transport, and later plugin-facing request surfaces.

## Non-Negotiable Invariants

- domain does not import infrastructure;
- external libraries stay behind ports/adapters;
- composition happens in bootstrap only;
- new domain seams should land atomically with adapter and wiring, not as orphan contracts;
- infrastructure placeholders must be explicitly treated as provisional rather than silently trusted as real implementations;
- requirement and finding provenance stay explicit;
- viewer state never becomes domain truth;
- Revit remains a client, not the center of the system.

## Bounded Contexts

### Validation Core

Owns normalized rules, IFC evaluation, IDS evaluation, findings, summaries, and reports.

### Requirement Normalization

Owns extraction from structured text, IDS, and later rich document packages into one internal DSL.

### Multimodal Analysis

Owns drawing annotation ingestion, 2D problem-zone payloads, and cross-document comparison between drawings, narrative sources, and BIM findings.

### Interop And Export

Owns BCF export, JSON/HTML export, and future OpenCDE adapter work.

### Review Surface

Owns browser issue review, filtering, provenance display, and navigation from finding to model context.

### Authoring Sync

Owns thin Revit-side issue pull, object focus, comments, and status pushback.

## Runtime Topology

### Backend

Python-first.

Reason:

- IfcOpenShell and IfcTester are strongest there;
- Docling is Python-native;
- the validation kernel is primarily data-processing and orchestration.

### Frontend

TypeScript-first.

Reason:

- browser viewing and issue triage fit the web;
- `web-ifc` and viewer ecosystems are JavaScript-native.

### Revit Client

Thin .NET-side boundary.

Reason:

- keep vendor gravity outside the domain runtime;
- let plugin logic focus on workflow, not validation truth.

## Adapter Strategy

### IfcOpenShell + IfcTester

Primary validation path.

### Docling

Document extraction input only. It may help produce candidate rules, but it must not be treated as the compliance engine.

### Narrative Rule Synthesizer

Use an infrastructure adapter to convert narrative TZ/calculation text into explicit normalized rules. The current baseline may be deterministic and heuristic; future LLM-backed adapters must still emit the same DSL with provenance.

### Drawing Analyzer

Use an infrastructure adapter to translate 2D drawing evidence into structured annotations and bounding-box problem zones. The current baseline may start from structured fixtures; future CV/VLM adapters must preserve the same contract.

### Remark Generator

Use an infrastructure adapter to convert findings into reviewer-friendly remarks. The generated remark is a convenience surface layered on top of explicit issue evidence, not the system of record.

### web-ifc

Default browser IFC parsing substrate.

### xeokit

Optional high-performance viewer adapter when federated scenes, XKT workflows, or richer viewer plugins justify the licensing decision.

### APS

Optional enterprise adapter for mixed-format translation and viewing. Useful for Revit-heavy enterprise scenarios, but not a core dependency.

### xBIM

Optional .NET-side adjunct for authoring-tool integrations. Useful if the plugin needs richer local IFC or IDS context.

### BIMserver

Optional server-side interop/storage benchmark and possible future adapter. Not required for the MVP kernel.

## Validation Pipeline

1. accept requirement input;
2. normalize into internal rule DSL;
3. ingest drawing annotations or future CV output;
4. execute IFC and IDS evaluation;
5. cross-check drawing evidence against normalized rules;
6. classify and materialize findings;
7. generate reviewer-friendly remarks;
8. persist report with provenance;
9. export JSON, HTML, then BCF;
10. surface findings in review UI and authoring clients.

## Delivery Rules Derived From MicroPhoenix

### Atomic Delivery

Every new capability should be delivered as a full runtime slice:

- contract;
- implementation;
- DI wiring;
- verification path;
- documentation update.

### Goal-Backward Completion

The implementation is not done because files exist. It is done when:

- the intended behavior is true;
- the required artifacts exist;
- the runtime path actually reaches them.

### Narrow-First Verification

Prefer the smallest sound verification pass first:

- changed-file diagnostics;
- targeted tests against fixtures or sample packs;
- then broader closure when the blast radius justifies it.

## Viewer And Revit Decisions

### Viewer

Start with a browser-first review surface. The product truth remains the report and its provenance, not viewer-internal state.

### Revit

Keep the plugin transport-thin. APS evidence confirms useful translation paths for Revit-linked models, but does not justify moving core validation into the authoring client.

## What Stays Out Of Canonical Architecture For Now

- Russian regulatory assertions without stable official citations;
- exact deep Revit desktop API claims that are not yet verified;
- precise complexity or throughput claims without benchmarks;
- license-sensitive dependencies being treated as default choices before legal review.

## Delivery Interpretation

At the current phase, the canonical interpretation is:

- backend validation scaffold exists and already exposes one multimodal project-package analysis path;
- frontend and plugin are still docs-first boundaries;
- the next meaningful milestone is replacing the local heuristic baselines with real IDS, CV, clash, and persistence adapters without changing the domain contracts.

Operational extraction details live in `08-microphoenix-adoption-matrix.md` and `09-implementation-and-verification-rails.md`.