# Sprint 2.1 LLM advisory comparison (mock)

**Claim level:** `synthetic_only`  
**Customer evidence:** false  
**Cloud API calls:** none (REPRODUCED mock)

> LLM comparison is **not** product accuracy evidence.

## Setup

- Port: `aerobim.domain.llm_advisory.LlmProvider`
- Providers under test: Kimi / Qwen / Gemma via `MockLlmProvider`
- Cases: `samples/benchmarks/llm-advisory/sprint-2-1-cases.json` (15 cases)
- Artifact: `artifacts/sprint-2-1/llm-comparison.json`
- Policy: `audit/llm_provider_policy.json` (`CLOUD_DATA_POLICY_UNKNOWN`)

## Ablation intent

| Mode | Deterministic findings | summary.outcome | summary.passed |
|---|---|---|---|
| deterministic only | baseline | unchanged | unchanged |
| + Kimi mock | identical | identical | identical |
| + Qwen mock | identical | identical | identical |
| + Gemma mock | identical | identical | identical |

Invariance enforced by `tests/test_llm_advisory_invariance.py` (REPRODUCED).

## Metrics focus (AEC)

schema_validity, evidence_reference_precision, unsupported_claim_rate, prompt_injection_resistance, verdict_invariance_rate — not BLEU/ROUGE.

## Forbidden

- Customer data to cloud without written permission
- LLM setting `summary.passed`
- Claiming cloud API safe for confidential packages
