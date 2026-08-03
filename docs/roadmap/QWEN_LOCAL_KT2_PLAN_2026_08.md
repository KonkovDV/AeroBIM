---
title: "Qwen / Yandex AI Studio — KT#2 executable plan"
status: active
version: "1.2.0"
last_updated: "2026-08-03"
claim_boundary: "Engineering plan. Alibaba Max forbidden. Yandex Studio RF = T2 PUBLIC/INTERNAL. Checkpoint NO_GO."
source_report: "docs/architecture/QWEN38_AEROBIM_FEASIBILITY_2026_08_03.md"
grant_note: "docs/architecture/YANDEX_AI_STUDIO_GRANT_KT2_2026_08_03.md"
deep_analysis: "docs/architecture/YANDEX_AI_STUDIO_AEROBIM_DEEP_ANALYSIS_2026_08_03.md"
---

# Qwen + Yandex AI Studio — KT#2 plan (4–20 Aug 2026)

## Decision lock

| Choice | Status |
|---|---|
| Alibaba `qwen3.8-max` | **FORBIDDEN** — `public_qwen38_max` NOT_VERIFIED |
| Yandex AI Studio cloud (RF grant) | **KT#2 T2** — PUBLIC/INTERNAL open corpora; same OpenAI-compat adapter |
| AI Studio on-prem / local vLLM | **Pilot T1** — CONFIDENTIAL/RESTRICTED path; change `base_url` only |
| GPU T4 grant track | **OCR/PDF render** — not LLM |
| Verdict / `summary.passed` | **UNTOUCHED** — OFF==ON |
| Entry scenario | **5.1** remark compose → **5.2** TZ→IDS → **5.3** VLM (**KT#2** via `qwen3.6-35b-a3b` multimodal; not deferred to KT#3) |

## Week 1 — landed / hardening

| ID | Deliverable | Status |
|---|---|---|
| W1-01…08 | Profile, adapter, compose CLI, OFF==ON, Claims wording | **Done** (`c52023c`) |
| W1-09 | Token budget caps per call/run/day (fail-closed) | **Done** |
| W1-10 | `private_yandex_ai_studio` profile + grant note | **Done** |
| W1-11 | Operator: activate grant before 2026-08-04; pin model URI | Operator |
| W1-12 | `audit_event.usage` + `probe_llm_reproducibility` scaffold | **Done** |

## Week 2 (11–20 Aug)

| ID | Deliverable |
|---|---|
| W2-01 | Scenario 5.2: LLM candidates → IDS/XSD verifier → WP-04 journal |
| W2-02 | Reproducibility experiment (`temperature=0`, +14d hash) → `reproducible` flag |
| W2-03 | `bench_hybrid_contour` + open-corpora timing; budget counters in artifacts |
| W2-04 | T4 track: batch OCR/render for EXTRACTION_INTEGRITY corpora |
| W2-05 | Claims Lock / matrix refresh for KT#2 drop |
| W2-06 | Scenario **5.3** region-crop VLM on Studio multimodal `qwen3.6-35b-a3b` (PUBLIC/INTERNAL open/fixture crops only). **Stamp/PII:** `plan_region_reads(exclude_stamp_regions=True)` + heuristic `layout_role=stamp` — default exclude before cloud call |

## KT#3 (Sep)

- On-prem Studio or local 3.8-27B after SBOM/license; same-corpus rebench.
- P₂ stability re-probe (+14d) and grant expiry vs self-pay (5.3 already in KT#2 window).

## Non-goals

Fine-tune · model-as-router · GraphRAG-as-product · autonomous agent · model output as finding on demo · T4 for 27B LLM.

## Verification

```bash
cd backend
python -m pytest tests/test_qwen_local_advisory.py tests/test_advisory_vlm_off_equals_on.py -q
python -m aerobim.tools.compose_advisory_remark --help
```
