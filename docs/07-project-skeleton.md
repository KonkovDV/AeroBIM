---
title: "AeroBIM Project Skeleton"
status: active
version: "0.4.0"
last_updated: "2026-04-12"
tags: [aerobim, skeleton, reference]
---

# AeroBIM Project Skeleton

## Intent

This file defines the current project skeleton and separates active runtime surfaces from boundary-first or placeholder surfaces.

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

Active runtime.

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

Expand backend behavior only through explicit domain contracts, adapters, tests, and composition-root wiring.

## Frontend

### Status

Active minimal runtime.

### Canonical Layout

```text
frontend/
├── public/
├── src/
├── package.json
├── vite.config.ts
└── tsconfig*.json
```

### Rule

The frontend currently owns review-shell concerns only: report list, issue detail, provenance, and export actions. It does not yet own a 3D viewer or 2D overlay workflow.

## Revit Plugin

### Status

Docs-first boundary.

### Canonical Layout

```text
clients/revit-plugin/
├── README.md
├── docs/
├── resources/
└── src/
```

### Rule

The plugin must stay thin. No validation truth should originate here.

## Samples

### Status

Active seed fixture surface.

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

These folders are the canonical home for representative fixtures used by tests, runtime smoke, and future benchmark rails.

## Ops

### Status

Active operational surface.

### Canonical Layout

```text
ops/
├── README.md
├── standalone-runbook.md
├── environment-matrix.md
├── storage-and-retention.md
└── smoke-path.md
```

### Rule

Keep bootstrap, environment, retention, and smoke guidance here instead of scattering it across unrelated docs.

## Current Placeholder Surfaces

- `clients/revit-plugin/src/README.md`
- `clients/revit-plugin/docs/README.md`
- `clients/revit-plugin/resources/README.md`

These remain intentional placeholders. The backend, frontend, ops, and sample packs are active surfaces.