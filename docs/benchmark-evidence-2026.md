---
title: "AeroBIM Benchmark Evidence 2026"
status: active
version: "1.0.0"
last_updated: "2026-07-19"
claim_boundary: "Fixture/synthetic metrics are not transferable to Samolet customer packs without re-measurement."
---

# Benchmark Evidence 2026

## What is measured (fixtures)

| Metric | Protocol / tool | Typical result | Transferable to Samolet? |
|---|---|---|---|
| RU extraction macro_f1 | `evaluate_extraction` | ≈0.86 on fixture GT | **No** — RT-001 |
| Detection precision harness | `evaluate_detection_precision` + synthetic labels | Contract gate ≥0.6 | **No** until customer labels |
| Package wall-clock | `benchmark_project_package` / `measure_package_sla` | Fixture-sized packs | **No** as ≤30 min customer claim |
| Ablation A0–A3 | `run_ablation_study` (historical; report may be local) | Multimodal contribution | **No** as product accuracy |
| Runtime baseline LOC/tests | `export_runtime_baseline` | See `evidence/runtime-baseline-latest.json` | N/A (engineering) |
| BCF structural T1 | `verify_bcf_structural_handoff` | Dual consumers agree | Structural only; not CDE |

Citeable snapshots under [`evidence/`](evidence/) and [`../audit/evidence/`](../audit/evidence/).

## Presentation rules

**Allowed:** “On frozen fixture pack X at commit SHA, macro_f1=… / wall-clock=…”.  
**Forbidden:** product accuracy %, customer комплект ≤30 min, Solibri replacement, CDE-ready BCF, MEP delivered.

## Sample sizes

Fixture corpora are small. Do not publish confidence intervals as if they were population estimates. Write: «на этом наборе получено X; переносимость не доказана».

## Customer path

Dual-human adjudication + κ/α + frozen split — see [`pilot-protocol-samolet-2026.md`](pilot-protocol-samolet-2026.md). Until intake gates flip, checkpoint stays **NO_GO**.
