---
title: "Qwen local advisory — KT#2 executable plan"
status: active
version: "1.0.0"
last_updated: "2026-08-03"
claim_boundary: "Engineering plan. Local open-weight advisory only. Cloud Max forbidden. Checkpoint NO_GO."
source_report: "docs/architecture/QWEN38_AEROBIM_FEASIBILITY_2026_08_03.md"
---

# Qwen local — KT#2 plan (4–20 Aug 2026)

## Decision lock (from report)

| Choice | Status |
|---|---|
| Cloud `qwen3.8-max` / Model Studio | **FORBIDDEN** — profile `public_qwen38_max` = `NOT_VERIFIED`, never default |
| Local open weights (3.6-27B / 35B-A3B now; 3.8-27B later) | **TARGET** |
| Verdict path / `summary.passed` | **UNTOUCHED** — OFF==ON must stay green |
| Entry scenario | **5.1** finding→remark RU/EN (then 5.2, then 5.3) |

## Week 1 (4–10 Aug) — in flight

| ID | Deliverable | Done when |
|---|---|---|
| W1-01 | Sample provider config with `private_qwen_local` + stub `public_qwen38_max` | File under `samples/hybrid/` |
| W1-02 | OpenAI-compat local LLM adapter (vLLM) + DI token | Tests with injectable transport; no network in CI |
| W1-03 | Settings `AEROBIM_LLM_*` for local endpoint / model / checkpoint hash | Fail-closed when unset |
| W1-04 | Domain compose: structured finding → `LlmRequest` → schema-guarded remark | Model cannot invent findings |
| W1-05 | CLI `compose_advisory_remark` (opt-in; not Analyze default) | Draft marked `ai_generated` + expert required |
| W1-06 | Capabilities honesty: `llm_advisory` reflects local/skipped/not_verified | SKIPPED ≠ FAILED for missing model |
| W1-07 | OFF==ON extended for LLM local flag | CI gate |
| W1-08 | Claims Lock / matrix allowed wording | No «Qwen 3.8 in product» |

**Out of Week 1:** real vLLM install in customer air-gap (operator runbook only); VLM crops (5.3); TZ→IDS compiler (5.2).

## Week 2 (11–20 Aug)

| ID | Deliverable |
|---|---|
| W2-01 | Scenario 5.2: LLM candidates → existing IDS/XSD verifier → WP-04 expert journal |
| W2-02 | `bench_hybrid_contour` metrics: latency, egress=0, schema-deviation |
| W2-03 | Open-corpora timing pins (BSI regression already vendored) |
| W2-04 | Claims Lock + capability matrix refresh for KT#2 drop |

## KT#3 (Sep)

- Migrate model id to Qwen3.8-27B **only** after SBOM/license gate + same-corpus rebench.
- Scenario 5.3 region-crop VLM + extraction-integrity second signal.
- Never claim Max / >90% / «ИИ проверяет нормы».

## Non-goals (hard)

Fine-tune · model-as-router · GraphRAG-as-product · autonomous agent pass · showing model output as a finding on demo.

## Verification

```bash
cd backend
python -m pytest tests/test_advisory_vlm_off_equals_on.py tests/test_qwen_local_advisory.py -q
python -m aerobim.tools.compose_advisory_remark --help
python -m aerobim.tools.export_runtime_baseline --check-readme --check-complete
```
