---
title: "AeroBIM Annotation Protocol 2026"
status: active
version: "1.2.0"
last_updated: "2026-07-10"
tags: [aerobim, annotation, benchmark, academic]
---

# Annotation Protocol — AEC Requirement Extraction Benchmark

## Purpose

Define a reproducible ground-truth schema for evaluating **deterministic** requirement extraction from narrative and structured technical documents (TZ / specifications / calculations), in **Russian and English**.

## Document inclusion criteria

1. Language: Russian (`ru`) or English (`en`).
2. Format: plain text narrative (`.txt`) or structured pipe-delimited lines.
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

## Inter-annotator agreement (IAA)

Dual annotation is required before promoting a fixture into the release gate corpus.

| Step | Action |
|------|--------|
| 1 | Two annotators independently fill [`samples/benchmarks/annotation/iaa-worksheet-template.json`](../samples/benchmarks/annotation/iaa-worksheet-template.json) |
| 2 | Labels: `requirement_span`, `ifc_entity`, `property_name`, `expected_value` |
| 3 | Compute **percent agreement** and **Cohen’s κ** on the label set |
| 4 | Accept fixture when κ ≥ **0.80** (substantial/almost perfect) **or** resolve disagreements and re-score |
| 5 | Store filled worksheet beside the fixture under `samples/benchmarks/annotation/` |

Cohen’s κ uses the standard chance-corrected formula on categorical labels; do not treat percent agreement alone as sufficient.

## Versioning

| Version | Fixtures | Requirements | Notes |
|---|---|---|---|
| 1.0.0 | 3 | 15 | Initial RU pilot set |
| 1.1.0 | 10 | 50 | Academic RU corpus extension |
| 1.2.0 | +2 EN | +10 | EN structured-text corpus + IAA worksheet |

Manifest SSOTs:

- RU: [`samples/benchmarks/russian-aec-ground-truth.json`](../samples/benchmarks/russian-aec-ground-truth.json)
- EN: [`samples/benchmarks/english-aec-ground-truth.json`](../samples/benchmarks/english-aec-ground-truth.json)

## Annotation directory

Optional per-fixture sidecars: [`samples/benchmarks/annotation/`](../samples/benchmarks/annotation/) — mirrors manifest entries for reviewer diff review.

## Ethics

Ground truth is authored for benchmark purposes; not copied from confidential customer documents.
