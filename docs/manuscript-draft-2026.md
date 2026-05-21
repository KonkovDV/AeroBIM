---
title: "AeroBIM Manuscript Draft 2026"
status: draft
language: en
---

# Deterministic Multimodal QA for OpenBIM Delivery: Method, Benchmark, and Pilot Case Study

## Abstract

We present AeroBIM, a reproducible deterministic kernel for cross-modal building information validation (IFC, IDS, narrative specifications, calculations, and drawing evidence) with explicit provenance and BCF export. On a curated Russian AEC extraction corpus (10 documents, 50 requirements), macro F1 ≥ 0.70 is enforced in CI. A multimodal ablation (A0–A3) quantifies the marginal value of narrative and cross-document layers. A Moscow pilot case study reports operational KPIs under a fixed claim boundary (no non-deterministic drawing sign-off).

## 1. Introduction

Fragmented QA across IFC, specifications, and calculations delays sign-off. AeroBIM targets **auditable** contradiction detection rather than non-reproducible verdicts.

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

Frozen pre-pilot line: tag `pilot-2026-pre`. Reports: [`docs/evidence/benchmark-report-2026-05-20.md`](evidence/benchmark-report-2026-05-20.md), [`docs/evidence/pre-pilot-extraction-2026-05-21.json`](evidence/pre-pilot-extraction-2026-05-21.json).

| Corpus | Documents | Requirements |
|---:|---:|---:|
| RU narrative | 10 | 50 |

Ablation configurations on frozen manifests (`pilot-2026-pre` evidence line):

| Mode | Layers | Issues | Requirements | Cross-doc |
|---|---|---:|---:|---:|
| A0 | IFC + IDS only | 2 | 0 | 0 |
| A1 | + narrative rules | 8 | 6 | 0 |
| A2 | + cross-document | 17 | 11 | 3 |
| A3 | Full pilot pack profile | 8 | 6 | 0 |

Source: [`evidence/ablation-study-report.json`](evidence/ablation-study-report.json), [`evidence/benchmark-report-2026-05-20.md`](evidence/benchmark-report-2026-05-20.md). A2 isolates marginal value of cross-document detection on the ablation fixture set; pilot Moscow fixtures may differ.

## 5. Case study — Pilot Moscow

Operational protocol: [`pilot-kpi-protocol-2026.md`](pilot-kpi-protocol-2026.md).

Detailed KPI table: [`pilot-case-study-report-2026.md`](pilot-case-study-report-2026.md).

## 6. Discussion

Limits: regex maintenance; fixture-only cross-document counts on the Moscow pilot pack must not be extrapolated to production models; no trained or non-deterministic adapters in the sign-off path; decision-support only (not licensed engineering compliance).

## Data availability

Reproduce frozen metrics from tag `pilot-2026-pre` (commit `1a5c03e`) using [`REPRODUCIBILITY-2026.md`](REPRODUCIBILITY-2026.md). Rolling `main` may add operator documentation without changing the frozen baseline commit.

## 7. Conclusion

AeroBIM provides a reproducible open benchmark and kernel suitable for ITcon / Automation in Construction supplementary material.

## Supplementary material

- `python -m aerobim.tools.generate_benchmark_report`
- GitHub release tag `v*` → `academic-benchmark-release.yml`
