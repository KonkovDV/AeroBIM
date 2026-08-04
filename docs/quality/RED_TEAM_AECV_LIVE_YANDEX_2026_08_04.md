---
title: "Red Team — live AECV-Bench on Yandex Qwen (open-bench only)"
status: active
version: "1.2.0"
last_updated: "2026-08-04"
claim_boundary: >-
  Public-floor-plan object-counting baseline only. Not AeroBIM product accuracy.
  closes_rt001=false. Checkpoint remains NO_GO. RT-001/002/003 open.
  Publish macro_bench_protocol (4 fields); macro_extended is internal.
---

# Red Team note — AECV live counting (2026-08-04)

## What was run

| Field | Value |
|---|---|
| Harness | AECV-Bench Use Case 1 (120 plans) |
| Provider | Yandex AI Studio |
| Model | `qwen3.6-35b-a3b` |
| Tool | `run_aecv_bench_eval --mode live` + `--mode enrich` |
| Thinking | `chat_template_kwargs.enable_thinking=false` |

## Two macros (do not conflate)

| Name | Definition | Value |
|---|---|---:|
| **`macro_extended`** (headline) | Five-field mean **including Space** = Table 1 / upstream `mean_accuracy` | **0.4325** |
| `macro_bench_protocol` | Mean EM over Door/Window/Bedroom/Toilet (paper prose / heatmap display) | **0.5064** |

Publish the first against Table 1. The second is reference-only — comparing it to Table 1 is a metric mismatch.

Attempted **120** / scored **117** / errors **3** (WEBP-as-JPEG MIME; ~9–11 KB under 12 KB soft floor). If errors counted as miss → five-field ≈**0.422**.

## Per-field (exact / MAPE / bias)

| Field | Exact | MAPE | Mean bias | Notes |
|---|---:|---:|---:|---|
| Door | 0.231 | 0.322 | −0.71 | |
| Window | 0.137 | 0.365 | **−2.58** | systematic undercount |
| Space | 0.137 | 0.294 | +0.21 | **in** Table 1 metric (upstream) |
| Bedroom | 0.846 | 0.128 | −0.03 | 16× pred0; 8 refusal |
| Toilet | 0.812 | 0.095 | −0.13 | |

Gradient matches paper §4: text-anchored rooms ≫ symbol doors/windows.

## vs paper Table 1 (same five-field metric)

`macro_extended` **0.4325** — below Gemini **0.51** / GPT-5.2 **0.49**, above Claude Opus 4.5 **0.42** and open GLM **0.39**.  
Wording: open model on RF cloud reaches frontier **order** — not «we beat Gemini». Gates: prompt §3.1.2, error policy, infra, model id — [`../research/AECV_BASELINE_COMPARE_2_1_2026_08_04.md`](../research/AECV_BASELINE_COMPARE_2_1_2026_08_04.md).

## Token economics (measured)

Full sheet prompt **2184**; completion ≈**47**; long-side 1024/512 → **1065/297**. Grant ops v1.9.

## Forbidden slides

- «Точность AeroBIM 43%/51%» / «>90%»
- «Мультимодальность пилота подтверждена»
- «RT-001 закрыт open-bench’ем»
- Only `macro_extended` next to paper means
