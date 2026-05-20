---
title: "Pilot Frozen Tag Protocol 2026"
status: active
version: "1.0.0"
last_updated: "2026-05-20"
tags: [aerobim, pilot, reproducibility]
---

# Pilot Frozen Tag Protocol

Freeze a reproducible evidence line before customer-facing pilot weeks and before any publication supplementary bundle.

## When to tag

1. After pre-pilot gates 1–3 are green ([`pilot-pre-pilot-gates-2026.md`](pilot-pre-pilot-gates-2026.md)).
2. Before the first production pilot ingest.
3. Again only if a **material** fix changes issue signatures (document in weekly log).

## Tag naming

`pilot-2026-wNN` or `pilot-2026-pre` for the pre-pilot baseline.

## Required artifacts on the tag

| Artifact | Command |
|---|---|
| Test suite | `pytest tests -q` |
| Extraction gate | `python -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70` |
| Benchmark report | `python -m aerobim.tools.generate_benchmark_report --output-dir ../docs/evidence` |
| Runtime baseline | `python -m aerobim.tools.export_runtime_baseline` |
| Conflict breakdown | `python -m aerobim.tools.summarize_conflict_breakdown` |

Store generated files under `docs/evidence/` with the tag name in the filename when publishing case-study evidence.

## CI expectation

The `academic-benchmark-release.yml` workflow runs on `v*` tags. For pilot-only tags use `pilot-*` and run the same commands locally; do not claim CI green unless the workflow was triggered.

## Corpus freeze rule

Do not add RU benchmark fixtures during the pilot window unless the weekly log records a scope change and gates 1–2 are re-run.
