---
title: "MicroPhoenix Adoption Matrix For AeroBIM"
status: active
version: "0.1.0"
last_updated: "2026-04-08"
tags: [aerobim, extraction, reference, architecture]
---

# MicroPhoenix Adoption Matrix For AeroBIM

## Purpose

This matrix turns the extraction story into explicit engineering decisions.

It answers one question for each major MicroPhoenix idea: should `AeroBIM` adopt it, adapt it, defer it, or reject it?

## Decision Vocabulary

- `adopt` — transfer with minimal conceptual change.
- `adapt` — keep the idea, but translate it to `AeroBIM` constraints.
- `defer` — valuable later, but too heavy for the current phase.
- `reject` — useful in MicroPhoenix, but misaligned with the BIM QA kernel.

## Architecture And Delivery Matrix

| MicroPhoenix concept | Decision | AeroBIM translation | Why |
|---|---|---|---|
| Inward dependency direction | `adopt` | `core -> domain -> application -> infrastructure -> presentation` | The principle transfers directly even though the original donor has a broader 10-layer model. |
| Explicit DI container | `adopt` | small Python container with token registry | `AeroBIM` benefits from explicit composition and replaceable adapters without reflection-heavy frameworks. |
| Central DI token registry | `adopt` | token constants under `backend/src/aerobim/core/di/` | Token SSOT reduces accidental wiring drift as adapters grow. |
| Single bootstrap composition root | `adopt` | one bootstrap entry for runtime wiring | This keeps startup deterministic and inspectable. |
| Entry-chain discipline | `adapt` | `main.py -> bootstrap -> http app` | The chain stays explicit, but the runtime is Python-first instead of Node-first. |
| Domain ports plus infrastructure adapters | `adopt` | Python `Protocol` contracts plus concrete adapters | This is the cleanest way to isolate IfcOpenShell, IfcTester, Docling, viewers, and future enterprise APIs. |
| Application use-case orchestration | `adopt` | one use-case class per business workflow | The project needs orchestration, but not controller-centric business logic. |
| LLM-assisted rule synthesis | `adapt` | narrative-rule-synthesizer port with deterministic fallback and future model-backed adapters | The competition task requires narrative TZ/calculation normalization, but the product still needs explicit DSL output and provenance. |
| 2D drawing/CV analysis | `adapt` | drawing-analyzer port with structured baseline and future CV/VLM adapters | Multimodal checking is required, but the first implementation can start from structured annotations instead of pretending to be full CV already. |
| Human-readable remark generation | `adapt` | remark-generator port with template baseline and future LLM enrichment | Reviewer-friendly remarks matter, but they must remain downstream of explicit findings rather than replacing them. |
| Request context and correlation discipline | `adapt` | explicit request and report provenance first; richer async context later | The idea transfers, but the current phase only needs durable request IDs and traceable report lineage. |
| Event sourcing plus Outbox-first delivery | `defer` | report-centric persistence now; event-first architecture later if needed | The idea is structurally sound, but too heavy before the product has stable workflows and real throughput pressure. |
| Typed event families | `defer` | start with stable domain report contracts; add typed events when async workflows deepen | Useful later for orchestration and auditability, but not required for the first validation kernel. |
| Multi-agent orchestration | `reject` for MVP | none in the runtime core | It solves donor-platform problems, not the first-order problem of deterministic BIM validation and review. |
| MCP server estate | `reject` for MVP runtime | none in runtime; docs may borrow discipline only | Internal developer tooling should not become the product runtime prematurely. |
| Memory and knowledge-graph subsystems | `defer` | none in MVP runtime | Valuable only after real report volume, retrieval needs, or cross-project knowledge reuse appear. |
| Anti-stub discipline | `adapt` | explicit provisional adapters, no silent fake completeness | The exact rule transfers, but should be phrased for Python and BIM adapters instead of TypeScript-only infrastructure. |
| Atomic delivery | `adopt` | contract + adapter + wiring + verification + docs | This prevents orphan ports and half-built capabilities. |
| Goal-backward verification | `adopt` | `truths`, `artifacts`, and `wiring` for each meaningful feature | This is directly useful for a product that must prove workflows, not just file edits. |
| Narrow-first verification | `adopt` | targeted diagnostics and sample-pack checks before broad gates | The principle transfers directly and reduces wasted validation cost. |
| Documentation authority and closure rails | `adapt` | local docs router plus root workspace docs closure rail | `AeroBIM` inherits the discipline, but currently closes docs through the parent workspace rail. |
| Search-before-build extraction discipline | `adopt` | inspect repo and standards first, then decide `adopt/adapt/defer/reject` | This is a donor idea worth keeping verbatim because it prevents abstraction sprawl. |
| Layer-specific always-on instruction mass | `reject` for AeroBIM docs | keep docs explicit and small | The product needs clarity, not a second control plane inside its own docs folder. |

## What This Means In Practice

### Already Adopted Or Adapted

- layer direction;
- DI tokens and bootstrap;
- use-case-oriented application layer;
- port/adapter seams;
- AI-ready ports for rule synthesis, drawing analysis, and remark generation;
- request and report provenance;
- docs-first architecture references.

### Intentionally Deferred

- event sourcing and typed event families;
- deep memory systems;
- high-complexity orchestration layers;
- large-scale plugin or marketplace surfaces.

### Explicitly Rejected For MVP

- donor platform complexity that does not accelerate IFC/IDS/report workflows;
- runtime surfaces whose main value is internal agent tooling rather than product behavior.

## Quality Bar For Future Extraction

An idea from MicroPhoenix should enter `AeroBIM` only if it passes all of these tests:

1. it reduces architectural risk in the BIM QA kernel;
2. it does not force product scope to expand prematurely;
3. it can be expressed in the current Python-first and browser-plus-plugin topology;
4. it comes with a plausible verification path, not just a conceptual appeal.