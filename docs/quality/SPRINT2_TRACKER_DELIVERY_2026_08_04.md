# Sprint 2 — deliverables for tracker meeting

**Date:** 2026-08-04  
**HEAD at write:** see git  
**Checkpoint:** **NO_GO** (RT-001/002/003 open; synthetics do not close)

## Deliverables checklist

| # | Item | Status | Path |
|---|---|---|---|
| 1 | Synthetic baseline PDF + JSON (recall/precision/Wilson/p95 + limitations) | **DONE** | [`docs/evidence/sprint2-synthetic-baseline-2026-08-04.pdf`](../evidence/sprint2-synthetic-baseline-2026-08-04.pdf) · [`.json`](../evidence/sprint2-synthetic-baseline-2026-08-04.json) · [`.md`](../evidence/sprint2-synthetic-baseline-2026-08-04.md) |
| 2 | Outreach contacts / demo agreed | **0 / 0** (operator) | [`docs/customer-discovery/sprint2-outreach-tracking.md`](../customer-discovery/sprint2-outreach-tracking.md) |
| 3 | Demo protocol with 3-category AI-only | **DONE** | [`docs/customer-demo/completed-project-comparison-protocol.md`](../customer-demo/completed-project-comparison-protocol.md) |
| 4 | Model bake-off table | **NOT_RUN** (no `AEROBIM_LLM_API_KEY` in this env) | [`docs/evidence/yandex-remarks-model-bakeoff-2026-08-04.json`](../evidence/yandex-remarks-model-bakeoff-2026-08-04.json) · harness `python -m aerobim.tools.run_yandex_remarks_bakeoff` |
| 5 | What we did **not** finish | below | — |

## Critical-path results (synthetic)

From baseline JSON (`claim_level=synthetic_only`):

| Metric | Value |
|---|---:|
| TP / FP / FN | 6 / 2 / 0 |
| Precision (point) | 0.75 |
| Precision Wilson lower (α=0.05) | ≈0.41 |
| Recall (point) | 1.0 |
| Recall Wilson lower | ≈0.61 |
| n planted detectable | 6 (below planner half-width 0.08) |
| time_per_case p95 | ~1.9 s (engine paths; not package SLA) |

Method: [`docs/pilot/SPRINT2_DETECTION_METRICS_METHOD_2026_08.md`](../pilot/SPRINT2_DETECTION_METRICS_METHOD_2026_08.md)  
GT: [`samples/benchmarks/sprint2-synthetic-ground-truth.json`](../../samples/benchmarks/sprint2-synthetic-ground-truth.json)

**Unplanted TZ classes (honest gaps):** geometric clash runnable pair; drawing↔model dimension pair. Covered partially/measured: area/LOAD, missing-element compensating control, IDS/TZ, FireRating contradiction.

## Block 6 verification

| Finding | Status |
|---|---|
| buildingSMART XSD `review_pending` | **CLOSED** (CC BY-ND 4.0; manifest `review_pending=0`) |
| Honesty surface keys + tests | **CLOSED** (`test_honesty_surface_contract.py`) |
| TZ row 27 MS Office | **PARTIAL** (explicit in matrix) |
| TZ row 28 version compare | **MISSING** (explicit; not hidden) |

Lecture ledger: [`docs/research/INDUSTRY_LECTURE_NOTES_LEDGER.md`](../research/INDUSTRY_LECTURE_NOTES_LEDGER.md)

## Not done (with reasons)

1. **Live multi-model bake-off** — API key absent; harness shipped.  
2. **Customer outreach numbers** — operator (table 0/0).  
3. **IFC-Bench v2 full run** — pins + license policy landed; local checkout + honest scored/total not yet executed.  
4. **BatchPlan / planted-on-real-IFC pipeline** — preferred over from-scratch synthetic; not wired yet.  
5. **ifcdiff / TZ row 28** — note landed; 0.8.5 wheel has no `ifcdiff` entry point; port still TODO.  
6. **KAAN / CubiCasa / Renga / Минстрой vendoring** — inventory/PARTIAL only.  
7. **RT-001** — needs labeled customer/archive pack.

## Follow-on from open-source search (2026-08-04)

See [`docs/dataset/OPEN_SOURCE_SEARCH_RESULTS_2026_08_04.md`](../dataset/OPEN_SOURCE_SEARCH_RESULTS_2026_08_04.md): prefer IFC-Bench v2 + BatchPlan planting; wrap ifcdiff-family diff for TZ row 28.

## Claims Lock reminder

Do not put AECV 0.43, «>90%», or «ИИ проверяет» into customer materials. Synthetic metrics ≠ product accuracy.
