---
title: "AeroBIM Annotation Protocol 2026"
status: active
version: "1.0.0"
last_updated: "2026-05-20"
tags: [aerobim, annotation, benchmark, academic]
---

# Annotation Protocol — Russian AEC Requirement Extraction Benchmark

## Purpose

Define a reproducible ground-truth schema for evaluating **deterministic** requirement extraction from Russian narrative technical documents (TZ / specifications / calculations).

## Document inclusion criteria

1. Language: Russian (`ru`).
2. Format: plain text narrative (`.txt`) mimicking TZ fragments.
3. Discipline tag: `architecture` | `structure` | `fire-safety` | `mep`.
4. Each document contains **5** atomic requirements mappable to IFC entities and properties.

## Requirement record schema

```json
{
  "rule_id": "R-DISC-NN",
  "ifc_entity": "IfcWall",
  "property_set": "Pset_WallCommon",
  "property_name": "FireRating",
  "expected_value": "REI120",
  "unit": null,
  "operator": "EQ|GE|LE",
  "rule_scope": "ifc-property"
}
```

## Matching rules (evaluation harness)

A predicted requirement is a **true positive** when:

1. `ifc_entity` matches (case-insensitive, `Ifc` prefix normalized).
2. `property_name` matches (case-insensitive).
3. `expected_value` matches (case-insensitive).
4. `property_set` checked when present in ground truth.
5. `unit` checked when present in both prediction and ground truth.

## Versioning

| Version | Fixtures | Requirements | Notes |
|---|---|---|---|
| 1.0.0 | 3 | 15 | Initial RU pilot set |
| 1.1.0 | 10 | 50 | Academic corpus extension |

Manifest SSOT: [`samples/benchmarks/russian-aec-ground-truth.json`](../samples/benchmarks/russian-aec-ground-truth.json).

## Annotation directory

Optional per-fixture sidecars: [`samples/benchmarks/annotation/`](../samples/benchmarks/annotation/) — mirrors manifest entries for reviewer diff review.

## Ethics

Ground truth is authored for benchmark purposes; not copied from confidential customer documents.
