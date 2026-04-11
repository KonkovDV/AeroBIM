---
title: "MicroPhoenix Extraction Dossier"
status: active
version: "0.3.0"
last_updated: "2026-04-08"
tags: [aerobim, extraction, architecture, explanation]
---

# MicroPhoenix Extraction Dossier

## Extraction Principle

`AeroBIM` does not clone MicroPhoenix. It extracts the subset of MicroPhoenix that creates durable architectural leverage for a BIM QA product.

The extraction rule is:

- keep patterns that improve modularity, traceability, and replaceability;
- reject patterns that belong to the original AI platform but do not accelerate BIM validation MVP value.

The working decision ladder for `AeroBIM` is:

- `adopt` when the MicroPhoenix pattern can transfer directly with minimal adaptation;
- `adapt` when the idea is sound but must be translated to a Python-first and product-narrow runtime;
- `defer` when the idea is valuable but would create premature operational weight;
- `reject` when the pattern solves the donor platform's problems, not the BIM QA kernel's problems.

## Source Patterns Confirmed In MicroPhoenix

The following patterns were verified from the live repository and treated as extraction-grade:

1. explicit DI container;
2. centralized token registry;
3. module-based bootstrap and composition root;
4. strict layer direction;
5. application-layer orchestration via use cases;
6. request-level traceability and config discipline.

## Extracted Patterns

| MicroPhoenix Surface | Extract Into AeroBIM | Why |
|---|---|---|
| `src/core/di/container.ts` | `backend/src/aerobim/core/di/container.py` | explicit runtime composition without reflection magic |
| `src/core/di/DI_TOKENS.ts` | `backend/src/aerobim/core/di/tokens.py` | token registry as SSOT for replaceable services |
| `src/infrastructure/di/bootstrap.ts` | `backend/src/aerobim/infrastructure/di/bootstrap.py` | single composition root and module binding point |
| `04-REFERENCE/architecture.md` | `core -> domain -> application -> infrastructure -> presentation` | preserve dependency direction and clean boundaries |
| thin entry chain | `main.py -> bootstrap -> http app` | keep startup deterministic and inspectable |
| port/adapter discipline | domain protocols + infra adapters | isolate IfcOpenShell, IfcTester, Docling, storage |

## Operational Ideas Extracted

The first pass extracted the architecture spine. The second pass extracts the delivery discipline around that spine.

### Atomic Delivery

New seams should land as complete units, not as aspirational interfaces.

For `AeroBIM`, that means:

- domain port or model;
- adapter;
- DI token and wiring;
- test fixture or proof path;
- documentation update.

### Goal-Backward Verification

Completion is defined by the outcome, not by the number of edited files.

For `AeroBIM`, every meaningful change should be checked against:

- `truths` — what must be true for the feature to exist;
- `artifacts` — which files and contracts must exist;
- `wiring` — which runtime paths must actually reach those artifacts.

### Anti-Stub Discipline

MicroPhoenix treats fake infrastructure as a source of architectural drift.

For `AeroBIM`, this becomes:

- do not pretend a validator validates if it only parses;
- do not pretend a report store persists if it is only a placeholder;
- if an adapter is intentionally provisional, mark and isolate it as provisional rather than letting it masquerade as production behavior.

### Verification Rails

MicroPhoenix uses explicit closure rails instead of informal "looks done" decisions.

For `AeroBIM`, the extracted idea is smaller but still strict:

- docs-only work closes through diagnostics and workspace docs closure;
- runtime work closes through targeted tests, sample-pack checks, and goal-backward verification.

### Search Before Building

MicroPhoenix donor extraction is explicit about not inventing new abstractions before checking what already exists.

For `AeroBIM`, that means:

- check current repo surfaces first;
- check authoritative external standards second;
- then decide whether to adopt, adapt, defer, or reject the candidate idea.

## Deliberately Not Extracted

| MicroPhoenix Capability | Why It Is Excluded From MVP |
|---|---|
| multi-agent orchestration | valuable for AI platform work, not required for deterministic BIM QA kernel |
| full event sourcing / outbox | too much operational weight before first validator is useful |
| MCP server fleet | internal platform tooling, not first-order product runtime |
| plugin marketplace | premature extensibility surface |
| vector memory / knowledge graph | not needed before the product has real issue and report volume |
| AOP-heavy aspects | can be added after runtime paths stabilize |

## Conceptual Translation Table

| MicroPhoenix Idea | AeroBIM Translation |
|---|---|
| domain ports | Python `Protocol` contracts |
| DI token registry | typed string token constants |
| module registration | bootstrap functions by bounded context |
| use case orchestration | one Python class per workflow |
| presentation boundary | HTTP API now, viewer/plugin later |
| request context | explicit `request_id` and later contextvars-based propagation |

## Bounded Contexts In AeroBIM

### Validation Core

Owns requirements, findings, reports, and rule evaluation.

### Interop

Owns IDS, BCF, openCDE, external file/package exchange.

### Review

Owns reviewer workflows, filtering, export, resolution states.

### Authoring Sync

Owns Revit / BIM-tool roundtrip only.

## Design Decisions Derived From Extraction

## Decision 1: Python-First Backend

MicroPhoenix is TypeScript-first, but `AeroBIM` should be Python-first because the target validation ecosystem is strongest there.

This is not a rejection of MicroPhoenix. It is a faithful translation of the same architectural shape into a better-suited runtime.

## Decision 2: One Narrow MVP Use Case

MicroPhoenix contains many subsystems because it is a platform.

`AeroBIM` starts with one narrow project-package use case:

- normalize structured and narrative requirements;
- reconcile them with drawing evidence;
- validate the IFC model;
- persist one explicit report with remarks and provenance.

Everything else hangs off that kernel.

## Decision 3: Adapters Must Hide Vendor Gravity

IfcOpenShell, IfcTester, Docling, viewer SDKs, and Revit APIs all stay behind ports.

The domain must not know which vendor or library performs the work.

## Decision 4: Delivery Discipline Is Part Of The Extraction

`AeroBIM` does not only extract folder structure. It also extracts the engineering posture around it.

That posture includes:

- explicit composition root ownership;
- atomic port-to-adapter delivery;
- explicit verification rails;
- refusal to treat placeholders as completed capabilities.

## Design Debt To Watch

1. token explosion;
2. bootstrap sprawl;
3. adapters leaking vendor types into domain objects;
4. viewer payloads becoming domain contracts;
5. narrative requirements being treated as validated facts before normalization.

## Minimum Safe Extraction Boundary

A safe first extraction is complete when these artifacts exist and are wired:

- container;
- token registry;
- settings loader;
- requirement extractor port + adapter;
- narrative rule synthesizer port + adapter;
- drawing analyzer port + adapter;
- IFC validator port + adapter;
- remark generator port + adapter;
- report store port + adapter;
- project-package analysis use case;
- HTTP endpoint calling the use case.

That is the smallest subset that preserves the MicroPhoenix discipline while producing product value.

## Where The Next Pass Lives

For exact keep/adapt/defer decisions, see `08-microphoenix-adoption-matrix.md`.

For the operational delivery rules derived from MicroPhoenix, see `09-implementation-and-verification-rails.md`.
