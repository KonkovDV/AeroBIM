---
title: "Samolet Implementation And Verification Rails"
status: active
version: "0.1.0"
last_updated: "2026-04-08"
tags: [samolet, how-to, verification, delivery]
---

# Samolet Implementation And Verification Rails

## Purpose

This document captures the operational discipline `Samolet` borrows from MicroPhoenix without copying the whole platform process model.

The goal is simple: keep delivery small, explicit, and verifiable.

## Core Rule

Do not treat a feature as complete because files exist.

A feature is complete only when:

- the intended behavior is true;
- the required artifacts exist;
- the runtime path actually reaches those artifacts.

## Smallest Safe Delivery Unit

For `Samolet`, the smallest safe unit is not just a file. It is a narrow vertical slice:

1. domain contract or model
2. infrastructure adapter or persistence implementation
3. DI token and bootstrap wiring
4. targeted verification path
5. documentation update if the architecture or contract changed

If one of these pieces is missing, the capability should be treated as incomplete.

## Atomic Delivery Rule

### When Adding A New External Capability

If a new external dependency enters the product, deliver it as a full slice:

- define the domain-facing contract first;
- keep vendor or library types out of the domain layer;
- add the adapter;
- wire it through bootstrap;
- add at least one proof path using fixtures or sample packs.

### When Extending Existing Behavior

Prefer extending a stable seam over inventing a new abstraction unless the current seam is clearly wrong.

Use the decision ladder:

- `adopt` if the existing pattern already fits;
- `extend` if the current seam is correct but incomplete;
- `compose` if multiple existing surfaces can be combined cleanly;
- `build` only if the repo and standards search prove a real gap.

## Domain-First Rule

When a change touches business behavior, start from the domain-facing contract or invariant.

For `Samolet`, this usually means starting from:

- requirement model;
- validation finding model;
- report summary model;
- extraction, validation, or persistence port.

Do not let adapters define product semantics by accident.

## Anti-Stub Rule

`Samolet` should inherit the donor's anti-stub posture in a product-appropriate form.

That means:

- a validator should either validate or clearly say that it does not yet validate;
- a persistence adapter should either persist or be explicitly marked as provisional;
- an AI or CV adapter should either emit explicit evidence-bearing outputs or clearly state that it is a limited baseline;
- placeholder behavior must stay local and visible rather than pretending to be production-ready.

## AI And CV Provenance Rule

If `Samolet` uses AI, NLP, or CV in any path, the adapter must still emit explicit normalized contracts:

- narrative sources must become `ParsedRequirement` objects with source provenance;
- drawing evidence must become `DrawingAnnotation` objects with optional problem zones;
- reviewer-friendly text must remain derivative of `ValidationIssue`, not a hidden side-channel.

No model output should become product truth without a typed intermediate contract.

## Goal-Backward Verification

Before implementing a meaningful feature, define three lists.

### Truths

Examples:

- a structured requirement pack becomes normalized rule objects;
- an IFC file produces deterministic findings;
- a report can be persisted and retrieved without losing provenance.

### Artifacts

Examples:

- domain models;
- ports;
- adapters;
- DI wiring;
- tests or fixtures.

### Wiring

Examples:

- HTTP route calls the use case;
- use case resolves ports from bootstrap;
- adapter touches the intended storage, parser, or validator path.

If the truths are not verified, the task is not complete even if the artifacts exist.

## Verification Lanes

### Docs-Only Lane

Use when the task changes documentation and project structure only.

Current closure rail in this workspace:

1. changed-file diagnostics
2. `npm run sync:metrics`
3. `npm run sync:metrics:check`
4. docs preflight through the parent workspace

### Backend Code Lane

Use when the Python backend changes.

Current minimum rail:

1. changed-file diagnostics
2. targeted tests under `backend/tests/`
3. fixture or sample-pack verification when relevant
4. broader closure when the blast radius justifies it

### Future Local Rail

As `Samolet` matures, it should gain its own local verification entrypoints for:

- backend tests and type checks;
- frontend checks;
- fixture-pack regression;
- report export regression.

## Sample-Pack Rule

Do not make performance or completeness claims without representative fixtures.

Use:

- `samples/specifications/` for TZ and narrative spec fixtures;
- `samples/calculations/` for calculation and threshold fixtures;
- `samples/drawings/` for drawing annotations or future CV output fixtures;
- `samples/requirements/` for structured rule inputs;
- `samples/ids/` for IDS packages;
- `samples/ifc/` for IFC models.

These packs are not optional decoration. They are the ground truth for future verification and benchmark claims.

## Documentation Rule

Any change that affects architecture, contracts, or boundaries should update the active docs in the same task.

At minimum, decide whether the change affects:

- `06-architecture-reference.md`
- `08-microphoenix-adoption-matrix.md`
- `04-atomic-backlog.md`
- this file

## Practical Checklists

### Before Building

- search the local repo first;
- check authoritative standards or vendor docs if the decision depends on them;
- decide whether the idea is adopt, adapt, defer, or reject;
- define truths, artifacts, and wiring.

### Before Closing

- verify the intended behavior, not just the file diff;
- verify that bootstrap reaches the new capability if it is meant to be live;
- verify that placeholder logic is not masquerading as production behavior;
- verify that the active docs still match the implementation.

## What This Document Deliberately Does Not Do

It does not copy the full MicroPhoenix 4-phase protocol, multi-agent operating model, or MCP-specific governance into `Samolet`.

The extracted value here is the disciplined subset that improves a small BIM QA product without importing donor-scale process overhead.