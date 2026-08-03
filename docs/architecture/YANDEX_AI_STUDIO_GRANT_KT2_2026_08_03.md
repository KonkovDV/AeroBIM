---
title: "Yandex AI Studio grant — KT#2/KT#3 contour implications"
date: 2026-08-03
status: active
version: "1.3.0"
claim_boundary: "Grant strategy note. Not Checkpoint GO. Card-bound → hard stop = revoke API key. Endpoint accepts images (HTTP 200); recognition quality NOT_MEASURED. enable_thinking=false is required for scenario 5.1 drafts."
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

## Billing defense (three layers — do not invert)

| Layer | What it does | What it does **not** |
|---|---|---|
| **L1 — YC billing budget** | **Notify only**. Period **month**, amount **6 000 ₽**. Thresholds 30% / 60% / 85% | Does **not** stop API calls |
| **L2 — AeroBIM ledger** | Fail-closed caps; day default **300 000** / run **100 000** (~two measured packs) | Does **not** see `curl` / console |
| **L3 — revoke API key** | `yc iam api-key delete <key-id>` — **immediate** stop of all Studio calls using that key; free; recreate in ~1 min | Does not stop spend that already used another key / console Playground |
| ~~L3 trial~~ | `TRIAL_EXPIRED` | **Unavailable** with bound MIR card |

Keep `key-id` next to budget alerts: 85% notification while away → revoke key first, investigate later. Prefer this over any Cloud Function.

### Model catalog — NOT_VERIFIED until live list

Operator console assistants listed YandexGPT 5.1 / 5 / 5 Lite, Alice AI LLM, DeepSeek V4 Flash — **no Qwen, no vision**. Official docs previously claimed `qwen3.6-35b-a3b` (262k + Base64 images) and `qwen3-235b-a22b-fp8` on the base instance. Those lists disagree with each other; **neither is SSOT**.

**SSOT = live API after SA key exists:**

```bash
curl -s -H "Authorization: Bearer $YC_API_KEY" \
  https://llm.api.cloud.yandex.net/foundationModels/v1/models \
  | python -m json.tool
```

| Outcome | Plan |
|---|---|
| Qwen (esp. multimodal) present | Keep KT#2 scenario 5.3 on Studio |
| Qwen absent | **Move 5.3 back to KT#3**; text advisory (5.1) on cheapest reliable text model now |

**Live 2026-08-03:** `POST /v1/chat/completions` with `gpt://{folder}/qwen3.6-35b-a3b` returned **200** (Api-Key and Bearer). `GET /foundationModels/v1/models` → **404**. Config uses **unversioned** URI (never write `/latest`); record `vendor_model_uri` from the response. **Vision:** endpoint **accepts** Base64 images (HTTP 200); **recognition quality NOT_MEASURED** — do not claim «мультимодальность подтверждена». Scenario 5.3 remains *in scope for KT#2* pending a crop-with-known-content check. **`enable_thinking=false` is mandatory** for text remark compose (5.1): without it `json_schema` burns completion into `reasoning_content` and returns empty `content`.

### Pricing (operator-reported; verify on live catalog)

| Model (label) | ~₽ / 1M in | ~₽ / 1M out | Use |
|---|---|---|---|
| YandexGPT 5.1 Pro | ~800 | ~800 | Target only after schema stable |
| DeepSeek V4 Flash | ~270 | ~450 | Mid |
| YandexGPT 5 Lite | ~200 | ~200 | **Default for prompt/schema debug** |

~200k-token pack on flagship ≈ **160 ₽** (not 100). Keep app caps at run 250k / day 300k until a measured pack cost in ₽.

**Live measure 2026-08-03 (think off):** one realistic IFC FireRating remark ≈ **440 tokens** (254p+186c). ×100 ≈ **44 000 tokens**. ₽ = × console tariff for `qwen3.6-35b-a3b` (still NOT_MEASURED in ₽). Probe A: `json_schema` OK with think off. Probe B: `seed` accepted (200); keep `send_seed=false` until P₁. G1 analyze overlay **wired**.

### Active grants (operator screenshot, 2026-08-03)

| Grant | Amount | Valid until | Notes |
|---|---|---|---|
| Main TechLab | **20 000 ₽** | **30.01.2027** | Covers KT#2 + KT#3 window |
| Starter | **4 000 ₽** | **02.10.2026** | Label «Все сервисы, кроме 4» — **must list exclusions**; if AI Studio excluded, usable Studio budget = 20 000 only |

Ask console/support (payment account `dn2gn7mktzezvuixvmsq`):

1. Name the four excluded services on the starter grant.  
2. Is Yandex AI Studio / Foundation Models excluded?  
3. Spend order of the two grants (earlier expiry first vs proportional)?  
4. After both grants empty with a bound card: auto-charge or confirmation required?  
5. Can the card be unbound **without** losing active grants? (If yes → restores free hard stop.)

Billing is at the **payment account** layer. Cloud `b1g29i9csghnoah26nne` / catalog `default` (`b1g56rei64gfdk5t2tvc`) clean ≠ all catalogs under the same payment account are idle — list every cloud/catalog and scan always-on resources.

### Card-bound reality (ops 2026-08-03)

- MIR ****3658 bound → treat as **paid path**: no `TRIAL_EXPIRED` free stop.  
- Real defense = AeroBIM ledger + discipline (no curl outside ledger without a separate mental budget).  
- Recalculate `MAX_TOKENS_*` after catalog **in/out** prices, not the ~0.5 ₽/1k average.
## Hard requirements before first Studio call

1. **App budget caps (fail-closed):** max tokens per call / per run / per day; charge estimate on transport failure and on every 429 retry; **`AEROBIM_LLM_BUDGET_LEDGER` required** for grant ops (without it: `budget_scope=process_local` — N workers ≈ N× daily cap); `AEROBIM_LLM_BUDGET_TZ` default `Europe/Moscow`. Stale `.lock` cleared by mtime; lock timeout → `lock_degraded=true` / `budget_scope=file_shared_lock_degraded` (RT-LEDGER-01). **TOCTOU (RT-LEDGER-02):** overshoot ≤ `N × max_tokens_per_call` — documented, not reserved.
2. **Structured findings only:** Qwen on Studio has **262 144** context tokens. Prompts = structured findings only (threat model + cost + provenance). Document text delimited as untrusted; **model never sets severity**.
3. **Yandex Completions quirks:** `model` = `gpt://{folder}/{name}/{version}`; prefer `json_schema` until Stage-0 curl proves otherwise; **do not send `seed`** until vendor confirms; `x-folder-id` + `x-data-logging-enabled: false`; `x-client-request-id` = opaque UUIDv4.
4. **Report reproducibility ≠ model determinism** (ADR-001). Pin exact model URI (no `/latest`/`/rc`).
5. **Stamp/PII crop gate:** unchanged; claim stays «PII-гейт активен; эффективность на реальных листах не измерена».
6. **Grant balance > 0 before any curl.** With a bound card, empty grants → auto charge — ledger is the only programmatic brake inside AeroBIM.

### Concurrent quota (confirmed)

| Fact | Value | Consequence for AeroBIM |
|---|---|---|
| Synchronous generations per cloud | **10** concurrent (confirmed for this grant contour) | Cloud-wide, shared with other workloads |
| Adapter limit | `BoundedSemaphore(4)` / `AEROBIM_LLM_MAX_CONCURRENT=4` | Fits with headroom for two parallel packs; **do not raise** without measuring 429 rate |

Operator checklist: cloud `b1g29i9csghnoah26nne`, folder `b1g56rei64gfdk5t2tvc`, SA `aerobim-ai-studio` + role `ai.languageModels.user`, API key scope `yc.ai.foundationModels.execute` (**show once → `.env` / secret store, never chat**), exact model URI+version from catalog, **budget 6 000 ₽/mo**, **ledger path set**.

## Live curl probe (only after grant balance > 0; do not edit adapter until answers known)

One request settles four unknowns: auth scheme, `json_schema` on OpenAI-compat, `seed` acceptance, and `x-data-logging-enabled` behaviour. Replace `<folder>`, `<key>`, `<version>` from the console catalog — never invent model ids.

```bash
# Probe A — json_schema (expected path)
curl -sS -X POST "https://llm.api.cloud.yandex.net/v1/chat/completions" \
  -H "Authorization: Bearer <key>" \
  -H "x-folder-id: <folder>" \
  -H "x-data-logging-enabled: false" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt://<folder>/qwen3.6-35b-a3b/<version>",
    "temperature": 0,
    "max_tokens": 128,
    "messages": [
      {"role": "system", "content": "Return JSON only."},
      {"role": "user", "content": "Compose {\"title\":\"t\",\"body\":\"b\",\"locale\":\"ru\",\"evidence_refs\":[\"e1\"]}"}
    ],
    "response_format": {
      "type": "json_schema",
      "json_schema": {
        "name": "advisory_remark",
        "schema": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "title": {"type": "string"},
            "body": {"type": "string"},
            "locale": {"type": "string", "enum": ["ru", "en"]},
            "evidence_refs": {"type": "array", "items": {"type": "string"}}
          },
          "required": ["title", "body", "locale", "evidence_refs"]
        }
      }
    }
  }'
```

```bash
# Probe B — seed (expect 400 if undocumented on this path; confirms AEROBIM_LLM_SEND_SEED=false)
curl -sS -X POST "https://llm.api.cloud.yandex.net/v1/chat/completions" \
  -H "Authorization: Bearer <key>" \
  -H "x-folder-id: <folder>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt://<folder>/qwen3.6-35b-a3b/<version>",
    "temperature": 0,
    "seed": 0,
    "max_tokens": 32,
    "messages": [{"role": "user", "content": "ping"}]
  }'
```

If Probe A fails on `json_schema`, fall back to `json_object` in env and keep schema validation in the adapter. If Probe B returns 400, keep `AEROBIM_LLM_SEND_SEED=false` (default for `yandex-ai-studio`).

## Analyze API wiring (KT#2 text contour)

`/v1/analyze/project-package` overlays LLM drafts onto deterministic issues via `overlay_llm_remarks` after template remarks. Drafts live on `issue.remark` with `ai_generated=true` (separate from engine severity). `capabilities.llm_advisory` is OK when drafts attach, SKIPPED when the model is unavailable or disabled — never FAILED, never flips `summary.passed`.

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
