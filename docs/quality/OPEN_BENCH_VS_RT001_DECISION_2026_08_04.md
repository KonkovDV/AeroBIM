---
title: "Decision — open AEC benchmarks vs RT-001 customer KPI"
status: active
version: "1.1.0"
last_updated: "2026-08-04"
claim_boundary: "Three number levels. Open-bench ≠ product accuracy. Checkpoint NO_GO until RT-001/002/003."
---

# Decision: customer KPI ≠ open-bench baseline

**Date:** 2026-08-04  
**Trigger:** Red Team A1 (`docs/quality/RED_TEAM_WORLD_PRACTICES_A1_A8_2026_08_04.md`)  
**Decision owner:** eng / Claims Lock guardian

## Decision

| Level | What it measures | When we publish | Closes RT-001? |
|---|---|---|---|
| **L1 — Open bench** | Public datasets (IFC-Bench, AECV-Bench, AEC-Bench, BSI IDS) under their licenses | Yes, with `claim_level=open_bench_only` | **No** |
| **L2 — Fixture / open corpora** | Repo pins, IDS↔IFC regression, timing | Yes, regression/timing only | **No** |
| **L3 — Customer adjudicated** | Dual-expert TP/FP on Samolet corpus + Wilson / κ/α | Only after intake | **Yes** (when gates pass) |

**RT-001 blocks L3 only.** Absence of L3 must never be used as an excuse to skip L1 when a free public harness exists.

## Why L1 now

- AEC-Bench (Apache 2.0) and AECV-Bench publish data + evaluation code without customer bytes.
- Literature already cited in-repo; without a run artifact the jury reads «won't measure».
- L1 numbers calibrate drawing-literacy / IFC-retrieval expectations; they are **not** Samolet precision.

## What landed (2026-08-04)

1. **IFC-Bench v1** — deterministic countable subset: **7/7** matched → [`../evidence/ifc-bench-v1-smoke-latest.json`](../evidence/ifc-bench-v1-smoke-latest.json).
2. **AECV-Bench object counting**
   - Offline rescore of published model JSONs (120 plans).
   - **Live** Yandex AI Studio `qwen3.6-35b-a3b`: 120 attempted / 117 scored / 3 errors; macro exact-match **0.4325** (Door 0.23 / Window 0.14 / Space 0.14 / Bedroom 0.85 / Toilet 0.81).
   - Evidence: [`../evidence/aecv-bench-eval-latest.json`](../evidence/aecv-bench-eval-latest.json) (`executive_summary`: MAPE, mean_bias, Bedroom refusal vs error, vs published Gemini/GPT macros) · Red Team note: [`RED_TEAM_AECV_LIVE_YANDEX_2026_08_04.md`](RED_TEAM_AECV_LIVE_YANDEX_2026_08_04.md).
   - Vendor quirk: send `chat_template_kwargs.enable_thinking=false` — top-level `enable_thinking` → HTTP 400. Images ≲12 KiB → HTTP 400 (`MIN_IMAGE_BYTES_VENDOR_REJECT`).
3. **AEC-Bench** — inventory 196 tasks + prefetch sample; Harbor **agent trial NOT_RUN** (needs separate agent key; Docker + Harbor CLI ready).
4. WP-06 open-corpora smoke remains L2.

## Reproduce live AECV (operator)

```text
# Credentials only in gitignored backend/.env (AEROBIM_LLM_*). Never paste keys in chat.
cd backend
python -m aerobim.tools.run_aecv_bench_eval --mode live --limit 120 --also-docs-evidence
```

Product advisory path stays off until `AEROBIM_LLM_LOCAL_ENABLED=true` + budget ledger.

## Forbidden

- Publishing L1/L2 as «точность AeroBIM» / «>90%» / Checkpoint GO.
- Criticizing TechLab stream peers by name in organizer-facing decks.
- Inventing scores without a committed evidence JSON under `docs/evidence/` or `artifacts/`.

## Non-engineer one-liner

Competitors can quote a percentage without a method. We publish three labeled levels: public-bench baseline, fixture regression, and customer-adjudicated precision — and we refuse to sell level 1 as level 3.
