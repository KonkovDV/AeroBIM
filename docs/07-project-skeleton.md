---
title: "AeroBIM Project Skeleton"
status: active
version: "0.3.0"
last_updated: "2026-04-10"
tags: [aerobim, skeleton, reference]
---

# AeroBIM Project Skeleton

## Intent

This file defines the project skeleton for the current phase.

The skeleton is deliberately conservative:

- keep existing backend scaffold intact;
- expand runtime only through bounded ports and adapters;
- add placeholder directories and boundary docs for surfaces not yet implemented.

## Current Top-Level Layout

```text
aerobim/
├── backend/
├── clients/
│   └── revit-plugin/
├── docs/
├── frontend/
├── ops/
└── samples/
```

## Backend

### Status

Already scaffolded.

### Canonical Layout

```text
backend/
├── pyproject.toml
├── pyrightconfig.json
├── src/
│   └── aerobim/
│       ├── core/
│       ├── domain/
│       ├── application/
│       ├── infrastructure/
│       └── presentation/
└── tests/
```

### Rule

Backend business logic may expand only through explicit domain contracts, adapters, and sample-backed verification.

## Frontend

### Status

Docs-first boundary with placeholder directories already present.

### Canonical Layout

```text
frontend/
├── README.md
├── public/
└── src/
```

### Rule

No viewer implementation yet. Use this space only for future review UI and viewer shells.

## Revit Plugin

### Status

Docs-first boundary with placeholder directories already present.

### Canonical Layout

```text
clients/revit-plugin/
├── README.md
├── docs/
├── resources/
└── src/
```

### Rule

The plugin must stay thin. No validation logic should originate here.

## Samples

### Status

Seed fixture packs are present for requirements, specifications, drawings, calculations, IDS, and IFC, while larger benchmark-grade packs still remain future work.

### Canonical Layout

```text
samples/
├── calculations/
├── drawings/
├── ifc/
├── ids/
├── requirements/
└── specifications/
```

### Rule

These folders are the canonical home for representative project fixtures used by architecture review, regression, and benchmark rails.

## Ops

### Status

Placeholder operational surface is present.

### Canonical Layout

```text
ops/
└── README.md
```

### Rule

Keep deployment notes, environment guidance, and future runbooks here instead of scattering them into unrelated docs.

## Immediate Skeleton Checklist

1. Keep `docs/06-architecture-reference.md` as the canonical architecture entrypoint.
2. Put sample IFC, IDS, and structured requirement packs into `samples/**` before expanding runtime logic.
3. Add drawing, specification, and calculation packs alongside the IFC/IDS fixtures for multimodal regression.
4. Keep frontend and Revit plugin docs-first until the validation/report core is usable.
5. Avoid adding vendor-specific runtime assumptions into `domain` or `application`.

## Current Placeholder Surfaces

- `frontend/src/README.md`
- `frontend/public/README.md`
- `clients/revit-plugin/src/README.md`
- `clients/revit-plugin/docs/README.md`
- `clients/revit-plugin/resources/README.md`
- `samples/calculations/README.md`
- `samples/drawings/README.md`
- `samples/requirements/README.md`
- `samples/specifications/README.md`
- `ops/README.md`

Most of these surfaces remain placeholders. The main exception is the backend runtime, which already contains the first multimodal analysis slice, plus seed IFC/IDS fixtures used by live end-to-end regression tests.