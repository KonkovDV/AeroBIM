---
title: "Yandex AI Studio grant — KT#2/KT#3 contour implications"
date: 2026-08-03
status: active
version: "1.2.0"
claim_boundary: "Grant strategy note. Not Checkpoint GO. Vendor pricing = claims. Cloud Alibaba Max still forbidden."
source_analysis: "docs/architecture/YANDEX_AI_STUDIO_AEROBIM_DEEP_ANALYSIS_2026_08_03.md"
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
2. **Structured findings only (not a 32k vendor limit):** Qwen on Studio has **262 144** context tokens (YandexGPT family is ~32k — not our path). Keep prompts to structured findings only for threat-model reasons: (i) minimize prompt-injection surface (`HYBRID_AI_THREAT_MODEL`); (ii) hold data class at INTERNAL; (iii) cost; (iv) provenance — the model must not see what it cannot cite. Do **not** justify this discipline by a non-applicable 32k cap.
3. **Yandex Completions quirks (adapter):** `model` = `gpt://{folder}/{name}/{version}` (not bare `Qwen…`); `response_format.type=json_schema` + `REMARK_JSON_SCHEMA`; **do not send `seed`** until vendor confirms; send `x-folder-id` + `x-data-logging-enabled: false` (recorded in usage/audit).
4. **Report reproducibility ≠ model determinism:** verdict stays deterministic-core only (ADR-001). Studio vendor probes (P₁/P₂) measure provider behaviour; they are **not** a publication gate. Still pin exact model URI (no `/latest`/`/rc`).
5. **Stamp/PII crop gate:** cloud VLM allowlists `layout_role=content` only, then clips stamp/title priors from the bbox; unknown role and unclippable pixel crops fail closed. Do not send stamp/title crops on C0/C1 without DPA / C2.
6. **Activate grant / payment account before 2026-08-04**; check grant expiry vs KT#3 window.

Operator checklist: folder ID, SA role `ai.languageModels.user`, API key scope `yc.ai.foundationModels.execute`, exact model version from AI Studio catalog.

## Bottleneck — grant is not RT-001

One WP-07 Wilson measure (n≈111 at half-width ≤0.08) costs on the order of **~111 ₽** (~1% of the AI Studio track). Token quota is not the critical path.

| Deficit | Blocks | Tracker ask |
|---|---|---|
| **Adjudicators** (2+) | RT-001 precision / expert TP/FP | Recruit / schedule adjudication — **do not** conflate with quota increase |
| **Customer corpus** | RT-001/002/003 evidence | Intake package + labeled ground truth |
| Token quota increase | Convenience / parallel burn | Useful, but **does not** move Checkpoint toward GO |

Do not mix “need more grant tokens” with “need adjudicators + corpus” in the same tracker ask — defense will notice.

## Contour levels C0–C3 (SLA ≠ classification)

ADR-002 remains the **open-core commercial boundary**. Studio routing uses an explicit contour ladder (see deep analysis §1.4). **C0 → C1 is an SLA measure, not a data-classification upgrade.**

| Level | Realization | What it improves | Allowed classes |
|---|---|---|---|
| **C0** | Shared AI Studio instance (RF) | — | PUBLIC, INTERNAL |
| **C1** | Dedicated AI Studio instance (RF) | latency, quotas, SLA predictability | PUBLIC, INTERNAL; **CONFIDENTIAL only with signed DPA** |
| **C2** | AI Studio on-premises in customer contour | egress boundary | CONFIDENTIAL, RESTRICTED |
| **C3** | External clouds outside RF | — | nothing; profile `NOT_VERIFIED` |

Raising class to CONFIDENTIAL requires a legal instrument (DPA), not a dedicated compute SKU.

## Classification (hybrid contour — not ADR-002 open-core)

ADR-002 is the **open-core commercial boundary** (LICENSE stays MIT). The Studio path closes the **Hybrid AI pilot-endpoint** gap in the routing policy:

| Contour label | Meaning for Studio |
|---|---|
| **T2 / private_shared** (≈ C0/C1 cloud) | Yandex AI Studio **cloud** (RF) — PUBLIC + INTERNAL open corpora for KT#2 |
| **T1 / private on-prem** (≈ C2) | AI Studio Docker/Helm / Stackland in Samolet contour — CONFIDENTIAL / RESTRICTED |
| Same adapter | `OpenAICompatLlmProvider`; only `AEROBIM_LLM_BASE_URL` (+ key) changes |

See [`../../audit/reports/HYBRID_AI_ROUTING_POLICY_2026_07_28.md`](../../audit/reports/HYBRID_AI_ROUTING_POLICY_2026_07_28.md).

## Claims Lock — allowed / forbidden

**Allowed:** «Пилотный advisory через Yandex AI Studio (RF) на открытых корпусах; тот же адаптер для on-prem Studio в контуре заказчика.»

**Forbidden:** «Данные Самолёта уходят в облако» · «Qwen 3.8 Max» · «точность >90% от модели» · «ИИ проверяет нормы» без IDS+expert · «увеличение квоты гранта = прогресс по RT-001».

## Bottleneck reminder

Grant tokens ≈ 1% cost of one WP-07 Wilson sample. Deficit for Checkpoint: **adjudicators + customer corpus**, not Studio ₽.

## Pointers

- Deep analysis: [`YANDEX_AI_STUDIO_AEROBIM_DEEP_ANALYSIS_2026_08_03.md`](YANDEX_AI_STUDIO_AEROBIM_DEEP_ANALYSIS_2026_08_03.md)
- Feasibility: [`QWEN38_AEROBIM_FEASIBILITY_2026_08_03.md`](QWEN38_AEROBIM_FEASIBILITY_2026_08_03.md)
- Plan: [`../roadmap/QWEN_LOCAL_KT2_PLAN_2026_08.md`](../roadmap/QWEN_LOCAL_KT2_PLAN_2026_08.md)
- Routing policy: [`../../audit/reports/HYBRID_AI_ROUTING_POLICY_2026_07_28.md`](../../audit/reports/HYBRID_AI_ROUTING_POLICY_2026_07_28.md)
