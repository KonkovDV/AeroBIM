---
title: "Red Team — live AECV-Bench on Yandex Qwen (open-bench only)"
status: active
version: "1.1.0"
last_updated: "2026-08-04"
claim_boundary: >-
  Public-floor-plan object-counting baseline only. Not AeroBIM product accuracy.
  closes_rt001=false. Checkpoint remains NO_GO. RT-001/002/003 open.
---

# Red Team note — AECV live counting (2026-08-04)

## What was run

| Field | Value |
|---|---|
| Harness | AECV-Bench Use Case 1 object counting (120 plans) |
| Provider | Yandex AI Studio |
| Model | `qwen3.6-35b-a3b` (`gpt://b1g56rei64gfdk5t2tvc/qwen3.6-35b-a3b`) |
| Tool | `run_aecv_bench_eval --mode live` → later `--mode enrich` (no re-spend) |
| Thinking | `chat_template_kwargs.enable_thinking=false` |
| Product LLM | `AEROBIM_LLM_LOCAL_ENABLED=false` |

## Numbers (exact-match + MAPE + bias)

| Field | Exact | MAPE | Mean bias (pred−exp) | Notes |
|---|---:|---:|---:|---|
| Door | 0.231 | 0.322 | **−0.71** | mild undercount |
| Window | 0.137 | 0.365 | **−2.58** | systematic skip (~3 windows) |
| Space | 0.137 | 0.294 | **+0.21** | same exact as Window, **different** failure mode |
| Bedroom | 0.846 | 0.128 | −0.03 | strong when answered |
| Toilet | 0.812 | 0.095 | −0.13 | strongest MAPE |
| **Macro** | **0.433** | — | — | 117 scored / 3 errors |

Attempted **120** / scored **117** / errors **3**.

Window and Space share exact-match 0.137 but coincide plan-wise only in **5/117** — coincidence, not shared mechanism.

## Refusal vs error (Bedroom)

| Signal | Count |
|---|---:|
| `Bedroom` predicted `0` | **16 / 117** |
| of which expected also `0` (correct zero) | 8 |
| of which expected `>0` (refusal/miss) | **8** |

For advisory: empty/zero miss is safer than a confident wrong positive. Report both rates; do not fold refusal into «accuracy».

## Published baseline comparison (same 120 plans, offline rescore)

| Model (published AECV JSON) | Macro exact |
|---|---:|
| `gemini_3_pro_preview` (best in checkout) | **0.523** |
| `gemini_31_pro` | 0.512 |
| `openai_gpt_52` | 0.485 |
| **Live Yandex Qwen 3.6-35b** | **0.433** |
| Δ live − best | **−0.091** |

Harness is in the same ballpark as mid/frontier published counters — not a broken scorer, not paper-SOTA. Prompt/resolution remain open levers; do not sell 0.43 as product KPI.

## Vendor image errors (corrected)

Errors `2000-0008/09/12` are **WEBP** files named `*.jpg` sent as `image/jpeg` → HTTP 400.  
Not a pure ~10 KiB size gate (synthetic JPEG ≈780 B → 200). Tool now sniffs magic bytes (`_image_mime`).

## Token / ₽ reading (measured)

| Measure | Value |
|---|---|
| Full sheet `prompt_tokens` | **2184** (522 KB PNG) |
| Range by file | **644–3850** |
| Long-side 1024 / 512 / 256 | **1065 / 297 / 105** (~quadratic) |
| `completion_tokens` (think off) | **≈47** |
| Tariff sketch | 200 ₽/M ⇒ ~0.44 ₽/sheet; 200 stamp crops ~20–30 ₽ |

Region-crop: **PII necessity** + ~3× ₽ saving vs full sheets — not a grant-killer.

Published baseline compare: live macro **0.433** vs best offline `gemini_3_pro_preview` **0.523** (Δ −0.091) — in `executive_summary`.

## Evidence

- [`../evidence/aecv-bench-eval-latest.json`](../evidence/aecv-bench-eval-latest.json) — `executive_summary` + enriched `per_field` (MAPE, mean_bias, zero rates)
- [`OPEN_BENCH_VS_RT001_DECISION_2026_08_04.md`](OPEN_BENCH_VS_RT001_DECISION_2026_08_04.md)

## Forbidden slides

- «Точность AeroBIM 43%» / «>90%»
- «Мультимодальность подтверждена для пилота»
- «RT-001 закрыт open-bench’ем»
