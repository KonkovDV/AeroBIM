---
title: "Yandex AI Studio grant ops — stage report"
date: 2026-08-03
status: ready_for_budget_then_enable
version: "1.9.0"
claim_boundary: "Not Checkpoint GO. Open-bench AECV counting measured (macro 0.4325) ≠ product accuracy. Vision token economics measured 2026-08-04. Thinking off via chat_template_kwargs only. Never paste API key."
ids: "folder b1g56rei64gfdk5t2tvc; kill-switch ajeomh7lns01j2lv3dcc"
---

# Grant ops v1.9 — multimodal token economics (measured)

## Limits (text advisory)

| Cap | Value | Why |
|---|---|---|
| `MAX_TOKENS_PER_RUN` | **100 000** | Measured ~44k/100 findings; old 250k ≈ 5 packs before trip |
| `MAX_TOKENS_PER_DAY` | **300 000** | Card-bound; no TRIAL_EXPIRED |
| Per remark | **~440 tok** (254p+186c, think off) | Real FireRating finding |

## Multimodal — measured input tokens (2026-08-04)

First **live** vision numbers on Yandex `qwen3.6-35b-a3b` (thinking off). Not estimates.

### By source file size (native AECV assets, live counting body)

| File bytes | `prompt_tokens` | Note |
|---:|---:|---|
| ≈63 KB JPEG | **644** | smaller plan |
| ≈522 KB PNG | **2184** | typical full sheet (`0000-0001`) |
| ≈789 KB PNG | **3850** | large plan |

File size ×12.5 (63→789 KB) ⇒ tokens ×≈6 — **not linear in file bytes**. Vendor resizes to an internal tile grid; **recompressing the file barely helps; shrinking pixel long-side does.**

### By pixel long-side (same plan `0000-0001`, PNG re-encode)

| Long side | `prompt_tokens` | Ratio vs previous |
|---:|---:|---|
| native ~1486 px | **2184** (earlier full-body measure) | — |
| **1024** | **1065** | ≈÷2 vs native |
| **512** | **297** | ≈÷3.6 vs 1024 (~quadratic) |
| **256** | **105** | ≈÷2.8 vs 512 |

**Confirmed:** halving the long side ≈ quartering prompt cost (order-of-magnitude). Working stamp resolution = cheapest long-side where stamp text stays readable (measure on real stamp crops next).

### Completion

With `chat_template_kwargs.enable_thinking=false`, counting replies use **`completion_tokens ≈ 47`**. Completion is negligible vs input at vision scale.

### ₽ sketch (operator tariff **200 ₽ / 1M tokens**)

| Unit | Prompt tok | ≈ ₽ |
|---|---:|---:|
| Full sheet | ~2200 | **~0.44** |
| Stamp crop (est. 500–800) | 500–800 | **~0.10–0.16** |
| 200 stamp crops / pack | — | **~20–30** |
| 120 full sheets @ native | — | **~53** |

Scenario **5.3 economically passes** with region-crop. Crop remains **necessary for PII/stamp gate**, not only for ₽ (3× saving is still good engineering).

Reproduce:

```text
cd backend
# credentials in gitignored .env only
python -m aerobim.tools.run_aecv_bench_eval --mode live --limit 1 ...
```

## Open-bench accuracy (not product KPI)

| Signal | Value |
|---|---|
| Live macro exact-match | **0.4325** (117/120) |
| Best published offline in checkout | `gemini_3_pro_preview` **0.523** |
| Δ live − best | **−0.091** |
| Window mean bias | **−2.58** (systematic undercount) |
| Space mean bias | **+0.21** (symmetric miss at same exact) |

Evidence: `docs/evidence/aecv-bench-eval-latest.json` → `executive_summary.published_baseline_comparison`.

## Vision 400s — root cause (corrected)

| Hypothesis | Verdict |
|---|---|
| «files ≲10 KB rejected» | **False as pure size gate** — synthetic JPEG **780 B** → HTTP **200** |
| AECV `2000-0008/09/12` | **WEBP** bytes, extension `.jpg`, sent as `image/jpeg` → **400** |
| Fix | Magic-byte MIME sniff (`_image_mime`); soft 12 KiB warn kept for ops |

## Ledger vs billing (open / first reading)

| Source | Tokens |
|---|---|
| Yandex billing detail (operator) | ~**368k** in / ~**9.6k** out |
| AeroBIM `var/llm_token_budget.json` `tokens_today` | **34** (product path only) |

**Gap:** open-bench CLI (`run_aecv_bench_eval`) talks to Studio **outside** the advisory ledger. First external-truth check ⇒ almost all vision spend bypassed AeroBIM counters. Follow-up: route bench tool through budgeted provider **or** accept CLI as out-of-ledger and reconcile manually after each L1 run.

## Mandatory: thinking off via `chat_template_kwargs`

| Placement | Vendor result |
|---|---|
| `chat_template_kwargs.enable_thinking=false` | **OK** |
| Top-level `enable_thinking` / `extra_body` | **HTTP 400** |

## Red Team audit

| Area | Verdict |
|---|---|
| Secrets in code/logs | Pass |
| ADR-001 / `summary.passed` | Pass |
| L1 sold as L3 | **Forbidden** |
| Vision economics | **Measured** (this section) |
| Ledger covers CLI vision | **Fail / known gap** |

Kill-switch: `yc iam api-key delete ajeomh7lns01j2lv3dcc`.

## Operator order

1. Console tariff pin (200 ₽/M used above — re-verify)  
2. Budget 6 000 ₽/мес + kill-switch at 85%  
3. Stamp-crop readability vs long-side 512/1024 matrix  
4. Close ledger gap for bench CLI or document as out-of-band  
5. Only then `AEROBIM_LLM_LOCAL_ENABLED=true` for product advisory
