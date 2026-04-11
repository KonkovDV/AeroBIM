---
title: "Atomic Backlog"
status: active
version: "0.2.0"
last_updated: "2026-04-08"
tags: [samolet, backlog, reference, delivery]
---

# Atomic Backlog

This backlog is intentionally narrow, explicit, and execution-ready. Each item is small enough to estimate, verify, and close without ambiguity.

## Stream A: Core Runtime

- `SAM-001` Create backend package skeleton and path layout.
- `SAM-002` Implement container registration and resolution semantics.
- `SAM-003` Add token registry for settings, extractor, validator, store, and use case.
- `SAM-004` Add environment-backed settings loader.
- `SAM-005` Define domain models for requirements, findings, summary, report, and request.
- `SAM-006` Define domain ports for extraction, validation, and report persistence.
- `SAM-007` Add bootstrap function that wires tokens to adapters and use cases.
- `SAM-008` Add unit tests for singleton and transient DI behavior.

## Stream B: Requirement Ingestion

- `SAM-020` Define a strict intermediate requirement DSL.
- `SAM-021` Add parser for structured requirement lines.
- `SAM-022` Add support for source provenance (`source_path`, `source_text`, `rule_id`).
- `SAM-023` Add validation for malformed requirement rows.
- `SAM-024` Add document-to-text extraction seam for Docling.
- `SAM-025` Add regression tests for requirement parsing.
- `SAM-026` Add sample requirement pack fixtures.
- `SAM-027` Add narrative TZ/calculation rule-synthesis baseline.
- `SAM-028` Add source-kind aware rule provenance fields.

## Stream C: IFC Validation Kernel

- `SAM-040` Implement IFC model open path through IfcOpenShell adapter.
- `SAM-041` Resolve entities by IFC type.
- `SAM-042` Resolve property sets and properties for target entities.
- `SAM-043` Add value comparison and mismatch findings.
- `SAM-044` Add missing-entity findings.
- `SAM-045` Add missing-property findings.
- `SAM-046` Add unsupported-rule findings.
- `SAM-047` Add deterministic summary aggregation.
- `SAM-048` Add fixture-based validator contract tests.
- `SAM-049` Add quantity and threshold validation.
- `SAM-050` Add target-reference matching against IFC element metadata.

## Stream D: IDS Path

- `SAM-060` Introduce explicit IDS input contract.
- `SAM-061` Add IfcTester-backed IDS validation adapter.
- `SAM-062` Normalize IfcTester output into domain findings.
- `SAM-063` Preserve rule identifiers from IDS specifications.
- `SAM-064` Add JSON and HTML export parity checks.
- `SAM-065` Add sample IDS + IFC regression pack.

## Stream E: Audit And Persistence

- `SAM-080` Define report persistence contract.
- `SAM-081` Replace in-memory store with filesystem or database store.
- `SAM-082` Persist report metadata, findings, and provenance together.
- `SAM-083` Add report retrieval endpoint.
- `SAM-084` Add report listing by project / discipline / run.
- `SAM-085` Add export-to-JSON endpoint.
- `SAM-086` Add export-to-HTML endpoint.
- `SAM-087` Add report snapshot tests.

## Stream F: Issue Transport

- `SAM-100` Define domain-to-BCF mapping rules.
- `SAM-101` Generate BCF topics from findings.
- `SAM-102` Attach IFC GUIDs and viewpoint metadata where available.
- `SAM-103` Add BCF zip export.
- `SAM-104` Add BCF REST adapter seam for later server integration.
- `SAM-105` Add roundtrip fixture tests for BCF export.

## Stream G: Presentation Surface

- `SAM-120` Add `/health` endpoint.
- `SAM-121` Add `/v1/validate/ifc` endpoint.
- `SAM-122` Add request validation and error mapping.
- `SAM-123` Add request ID generation when absent.
- `SAM-124` Add report retrieval HTTP endpoint.
- `SAM-125` Add OpenAPI description review.
- `SAM-126` Add API smoke tests.
- `SAM-127` Add `/v1/analyze/project-package` endpoint.

## Stream H: Multimodal Cross-Check

- `SAM-140` Add structured drawing annotation contract.
- `SAM-141` Add drawing annotation parser for text and JSON fixtures.
- `SAM-142` Add drawing-to-rule comparison logic.
- `SAM-143` Add problem-zone payload with 2D bounding box support.
- `SAM-144` Add template remark generation for designers.
- `SAM-145` Add sample packs for drawings, specifications, and calculations.
- `SAM-146` Add contract tests for the project-package analysis flow.

## Stream I: Frontend Review Surface

- `SAM-150` Create React/Vite viewer shell.
- `SAM-151` Integrate web-ifc loader.
- `SAM-152` Render issue list and severity filters.
- `SAM-153` Link issue selection to element highlight.
- `SAM-154` Add requirement-to-finding drilldown.
- `SAM-155` Add export actions for JSON / HTML / BCF.
- `SAM-156` Add viewer performance checks on large models.

## Stream J: Revit / Authoring Sync

- `SAM-160` Define thin plugin transport contract.
- `SAM-161` Add issue fetch command from backend.
- `SAM-162` Add object focus / isolate workflow.
- `SAM-163` Add comment / status pushback command.
- `SAM-164` Add auth and project binding flow.
- `SAM-165` Add plugin packaging and deployment notes.

## Stream K: Interop And Scale

- `SAM-180` Add project / tenant isolation model.
- `SAM-181` Add asynchronous job execution for large models.
- `SAM-182` Add openCDE foundation/documents interoperability adapters.
- `SAM-183` Add structured metrics for validation throughput.
- `SAM-184` Add storage durability and retention policy.
- `SAM-185` Add benchmark pack for large-model validation.

## Recommended Execution Order

1. `SAM-001` through `SAM-008`
2. `SAM-020` through `SAM-026`
3. `SAM-027` through `SAM-028`
4. `SAM-040` through `SAM-050`
5. `SAM-120` through `SAM-127`
6. `SAM-140` through `SAM-146`
7. `SAM-080` through `SAM-087`
8. `SAM-060` through `SAM-065`
9. `SAM-100` through `SAM-105`
10. `SAM-160` through `SAM-165`
11. `SAM-180` through `SAM-185`

## Verification Rule

No stream is considered complete until:

- artifacts exist;
- they contain substantive code or explicit contract documentation;
- the bootstrap/runtime path reaches them;
- at least one automated verification path covers them.
