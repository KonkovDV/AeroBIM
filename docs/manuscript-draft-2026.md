---
title: "AeroBIM Manuscript Draft 2026"
status: draft
language: en
---

# Deterministic Multimodal QA for OpenBIM Delivery: Method, Benchmark, and Pilot Case Study

## Abstract

We present AeroBIM, a reproducible deterministic kernel for cross-modal building information validation (IFC, IDS, narrative specifications, calculations, and drawing evidence) with explicit provenance and BCF export. On a curated Russian AEC extraction corpus (10 documents, 50 requirements), macro F1 ≥ 0.70 is enforced in CI. A multimodal ablation (A0–A3) quantifies the marginal value of narrative and cross-document layers. A Moscow pilot case study reports operational KPIs under a fixed claim boundary (no VLM sign-off).

## 1. Introduction

Fragmented QA across IFC, specifications, and calculations delays sign-off. AeroBIM targets **auditable** contradiction detection rather than opaque LLM verdicts.

## 2. Related work

- Hybrid ACC rule-first pipelines (ITcon 2025 SLR)
- IFC-QA multimodal benchmarks
- buildingSMART IDS 1.0 delivery contracts
- ISO/DIS 19650-1 information management lifecycle

## 3. Method

- 10-layer clean architecture with deterministic extractors
- `ConflictKind`: `unit-mismatch`, `hard-conflict`, `ambiguous-mapping`
- UCUM-aligned `si_compare` with ε-tolerance
- LOIN metadata (`purpose`, `milestone`, `actor`) in exports
- External evidence port (OpenRebar implementation)

## 4. Benchmark

See generated report: `docs/evidence/benchmark-report-*.md`.

| Corpus | Documents | Requirements |
|---:|---:|---:|
| RU narrative | 10 | 50 |

Ablation configurations: A0 (IFC+IDS) → A3 (full pilot pack).

## 5. Case study — Pilot Moscow

Operational protocol: [`pilot-kpi-protocol-2026.md`](pilot-kpi-protocol-2026.md).

Detailed KPI table: [`pilot-case-study-report-2026.md`](pilot-case-study-report-2026.md).

## 6. Discussion

Limits: regex maintenance, fixture scope, no fine-tuned model in sign-off path.

## 7. Conclusion

AeroBIM provides a reproducible open benchmark and kernel suitable for ITcon / Automation in Construction supplementary material.

## Supplementary material

- `python -m aerobim.tools.generate_benchmark_report`
- GitHub release tag `v*` → `academic-benchmark-release.yml`
