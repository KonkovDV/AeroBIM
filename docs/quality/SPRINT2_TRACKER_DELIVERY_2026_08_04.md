# Sprint 2 — deliverables for tracker meeting

**Date:** 2026-08-04  
**HEAD at write:** see git  
**Checkpoint:** **NO_GO** (RT-001/002/003 open; synthetics do not close)

## Deliverables checklist

| # | Item | Status | Path |
|---|---|---|---|
| 0 | **Пакет к трек-встрече 07.08 (К0)** | **INDEX** | [`TRACKER_MEETING_PACK_2026_08_07.md`](TRACKER_MEETING_PACK_2026_08_07.md) |
| 1 | Tracker baseline PDF + TZ row map (+ synthetic twin) | **DONE** | [`docs/evidence/tracker-baseline-2026-08-07.pdf`](../evidence/tracker-baseline-2026-08-07.pdf) · [`.md`](../evidence/tracker-baseline-2026-08-07.md) · synthetic [`sprint2-synthetic-baseline-2026-08-04.pdf`](../evidence/sprint2-synthetic-baseline-2026-08-04.pdf) |
| 2 | Outreach: org list 30+ / contacted / demo | **28 SSOT orgs / 0 / 0** (legacy sprint2 CSV=40 superseded) | локально (не в GH): `.local/commercial-ops/commercial-pipeline.csv` · `.local/commercial-ops/outreach-log.md` |
| 3 | Demo protocol with 3-category AI-only | **DONE** | [`completed-project-comparison-protocol.md`](../customer-demo/completed-project-comparison-protocol.md) · RU [`DEMO_SCENARIO_TRACKER_RU_2026_08.md`](../customer-demo/DEMO_SCENARIO_TRACKER_RU_2026_08.md) |
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
3. **BatchPlan / planted-on-real-IFC pipeline** — MIT tool pinned; **pythonocc** blocker; not wired. See [`BATCHPLAN_PROBE_2026_08_04.md`](../dataset/BATCHPLAN_PROBE_2026_08_04.md). KAAN project data **do not vendor** ([`KAAN_LICENSE_HONESTY_2026_08_04.md`](../dataset/KAAN_LICENSE_HONESTY_2026_08_04.md)).  
4. **ifcdiff / TZ row 28** — thin `Tokens.IFC_MODEL_DIFF` + fixture landed; matrix row 28 stays **MISSING** (CDE compare). See [`IFCDIFF_TZ_GAP_NOTE_2026_08_04.md`](../dataset/IFCDIFF_TZ_GAP_NOTE_2026_08_04.md).  
5. **KAAN / CubiCasa / Renga / Минстрой vendoring** — inventory/PARTIAL only.  
6. **RT-001** — needs labeled customer/archive pack.

## Done this wave (honest denominators)

- **IFC-Bench v2 smoke** — measured pin `e47ccd…`, scored **7/1026** @ 1.0 on countable subset; evidence [`ifc-bench-v2-smoke-latest.json`](../evidence/ifc-bench-v2-smoke-latest.json). Not full-bench accuracy.

## Follow-on from open-source search (2026-08-04)

See [`docs/dataset/OPEN_SOURCE_SEARCH_RESULTS_2026_08_04.md`](../dataset/OPEN_SOURCE_SEARCH_RESULTS_2026_08_04.md): prefer IFC-Bench v2 + BatchPlan planting; wrap ifcdiff-family diff for TZ row 28.

## Claims Lock reminder

Do not put AECV 0.43, «>90%», or «ИИ проверяет» into customer materials. Synthetic metrics ≠ product accuracy.
