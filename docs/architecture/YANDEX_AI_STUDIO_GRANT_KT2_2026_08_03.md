---
title: "Yandex AI Studio grant — KT#2/KT#3 contour implications"
date: 2026-08-03
status: active
version: "1.0.0"
claim_boundary: "Grant strategy note. Not Checkpoint GO. Vendor pricing = claims. Cloud Alibaba Max still forbidden."
---

# Yandex grant: AI Studio + GPU T4 (2026-08-03)

## Why this changes the board

Same OpenAI-compat adapter already in AeroBIM (`OpenAICompatLlmProvider`). Contour path becomes:

| Phase | Endpoint | Classification (ADR hybrid) | Adapter |
|---|---|---|---|
| **KT#2 now** | Yandex AI Studio cloud (RF, no data abroad) | **T2 / private_shared** — PUBLIC + INTERNAL open corpora only | `base_url` → Studio |
| **Pilot Samolet** | AI Studio **on-premises** (Docker/Helm / Stackland, private endpoints, no internet egress) | **T1 / private** — CONFIDENTIAL / RESTRICTED eligible under customer policy | same adapter, `base_url` change |
| **Forbidden** | Alibaba `qwen3.8-max` / Model Studio CN | PUBLIC egress blocked for CONFIDENTIAL/RESTRICTED | profile `public_qwen38_max` stays NOT_VERIFIED |

Competitor “fully Russian stack on Yandex Cloud” is no longer a unique wedge: AeroBIM keeps deterministic core + Claims Lock + the same RF vendor path.

## Grant split (do not invert)

| Track | Budget | Use | Do **not** use for |
|---|---|---|---|
| **1 — AI Studio** | ~16 000 ₽ | Advisory remark compose + TZ→IDS candidates; regression remesures | Unlimited repair-loops |
| **2 — GPU T4** | ~4 000 ₽ | Batch OCR + PDF render corpora (`EXTRACTION_INTEGRITY`, render-vs-extract) | Hosting Qwen 27B (T4 16 GB cannot) |

Rough burn (vendor-order-of-magnitude): ~100 findings ≈ 250k tokens ≈ ~100 ₽ → grant ≈ 100–150 full pack runs if capped.

## Hard requirements before first Studio call

1. **Budget caps (fail-closed):** max tokens per call / per run / per day; counters in usage/audit; exceed → no call.
2. **Context 32k:** only structured findings enter the prompt (architecture already enforces this).
3. **Yandex Completions quirks (adapter):** `model` = `gpt://{folder}/{name}/{version}` (not bare `Qwen…`); `response_format.type=json_schema` + `REMARK_JSON_SCHEMA`; **do not send `seed`** until vendor confirms; send `x-folder-id` + `x-data-logging-enabled: false` (recorded in usage/audit).
4. **Reproducibility:** Studio profile stays `reproducible=false` until `probe_llm_reproducibility` matches twice on a pinned version (not `latest`).
5. **Activate grant / payment account before 2026-08-04**; check grant expiry vs KT#3 window.

Operator checklist: folder ID, SA role `ai.languageModels.user`, API key scope `yc.ai.foundationModels.execute`, exact model version from AI Studio catalog.

## Classification (hybrid contour — not ADR-002 open-core)

ADR-002 is the **open-core commercial boundary** (LICENSE stays MIT). The Studio path closes the **Hybrid AI pilot-endpoint** gap in the routing policy:

| Contour label | Meaning for Studio |
|---|---|
| **T2 / private_shared** | Yandex AI Studio **cloud** (RF) — PUBLIC + INTERNAL open corpora for KT#2 |
| **T1 / private on-prem** | AI Studio Docker/Helm / Stackland in Samolet contour — CONFIDENTIAL / RESTRICTED |
| Same adapter | `OpenAICompatLlmProvider`; only `AEROBIM_LLM_BASE_URL` (+ key) changes |

See [`../../audit/reports/HYBRID_AI_ROUTING_POLICY_2026_07_28.md`](../../audit/reports/HYBRID_AI_ROUTING_POLICY_2026_07_28.md).

## Claims Lock — allowed / forbidden

**Allowed:** «Пилотный advisory через Yandex AI Studio (RF) на открытых корпусах; тот же адаптер для on-prem Studio в контуре заказчика.»

**Forbidden:** «Данные Самолёта уходят в облако» · «Qwen 3.8 Max» · «точность >90% от модели» · «ИИ проверяет нормы» без IDS+expert.

## Pointers

- Feasibility: [`QWEN38_AEROBIM_FEASIBILITY_2026_08_03.md`](QWEN38_AEROBIM_FEASIBILITY_2026_08_03.md)
- Plan: [`../roadmap/QWEN_LOCAL_KT2_PLAN_2026_08.md`](../roadmap/QWEN_LOCAL_KT2_PLAN_2026_08.md)
- Routing policy: [`../../audit/reports/HYBRID_AI_ROUTING_POLICY_2026_07_28.md`](../../audit/reports/HYBRID_AI_ROUTING_POLICY_2026_07_28.md)
