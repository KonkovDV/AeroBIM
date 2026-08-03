---
title: "Decision — open AEC benchmarks vs RT-001 customer KPI"
status: active
version: "1.2.0"
last_updated: "2026-08-04"
claim_boundary: "Three number levels. Open-bench ≠ product accuracy. Checkpoint NO_GO until RT-001/002/003."
---

# Decision: customer KPI ≠ open-bench baseline

**Date:** 2026-08-04  
**Trigger:** Red Team A1 + AECV paper §6 (arXiv:2601.04819)  
**Decision owner:** eng / Claims Lock guardian

## Decision

| Level | What it measures | When we publish | Closes RT-001? |
|---|---|---|---|
| **L1 — Open bench** | Public datasets (IFC-Bench, AECV-Bench, AEC-Bench, BSI IDS) under their licenses | Yes, with `claim_level=open_bench_only` | **No** |
| **L2 — Fixture / open corpora** | Repo pins, IDS↔IFC regression, timing | Yes, regression/timing only | **No** |
| **L3 — Customer adjudicated** | Dual-expert TP/FP on Samolet corpus + Wilson / κ/α | Only after intake | **Yes** (when gates pass) |

**RT-001 blocks L3 only.** Absence of L3 must never be used as an excuse to skip L1 when a free public harness exists.

## Why L1 ≠ RT-001 — authors say so

AECV-Bench §6 (Kondratenko et al., arXiv:2601.04819, **VERIFIED** full text) limits the corpus to ~120 public floor plans (CubiCasa5K / CVC-FP / open sources), **raster only** (no native CAD/BIM), **single images** without cross-sheet references, and **four** object classes. That is written justification that L1 cannot close customer dual-expert precision (RT-001).

## Why L1 now

- Transparent published protocol + baselines (paper Tables 1–2).
- Without a run artifact the jury reads «won't measure».
- L1 calibrates drawing-literacy expectations; **not** Samolet precision.

## What landed (2026-08-04)

1. **IFC-Bench v1** — 7/7 countable → [`../evidence/ifc-bench-v1-smoke-latest.json`](../evidence/ifc-bench-v1-smoke-latest.json).
2. **AECV-Bench object counting**
   - Live Yandex `qwen3.6-35b-a3b`: 120/117/3.
   - **Publish:** `macro_bench_protocol` = **0.5065** (Door/Window/Bedroom/Toilet — paper protocol).
   - **Internal:** `macro_extended` = **0.4325** (adds Space; not in Tables 1–2).
   - MAPE + mean_bias in `executive_summary` (Window bias −2.58).
   - Evidence: [`../evidence/aecv-bench-eval-latest.json`](../evidence/aecv-bench-eval-latest.json) · compare note: [`../research/AECV_BASELINE_COMPARE_2_1_2026_08_04.md`](../research/AECV_BASELINE_COMPARE_2_1_2026_08_04.md).
   - Public Table-1 compare only after comparability gates (prompt §3.1.2, error handling, infra, model id).
3. **AEC-Bench** — inventory; Harbor agent NOT_RUN.
4. WP-06 open-corpora = L2.

## Forbidden

- Publishing L1/L2 as «точность AeroBIM» / «>90%» / Checkpoint GO.
- Publishing only `macro_extended` next to paper means without stating Space.
- Criticizing TechLab peers by name in organizer decks.

## Non-engineer one-liner

We publish three labeled levels. Open benches (with the authors' own limitations quoted) are not customer precision — and we still refuse to sell level 1 as level 3.
