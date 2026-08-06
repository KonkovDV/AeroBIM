# LLM comparative benchmark

**claim_level:** `fixture_only` (mock) · live bake-off optional  
**Tool:** `backend/src/aerobim/tools/benchmark_llm_advisory.py`  
**Cases:** `samples/benchmarks/llm-advisory/sprint-2-1-cases.json`

## Purpose

Compare advisory providers (Kimi / Qwen / Gemma abstractions) on **fixture** cases without publishing product accuracy.

## Artifact schema (v1.1)

| Field | Notes |
|---|---|
| `claim_level` | `fixture_only` when mock / no API keys |
| `customer_precision_claim_publishable` | always `false` here |
| `affects_summary_passed` | always `false` |
| `rows[].latency_ms` | mock wall time (schema completeness) |
| `rows[].cost` | `null` unless a live tool supplies it |
| `rows[].json_validity` / `schema_valid` | schema guard |
| `rows[].agreement_with_deterministic` | placeholder vs deterministic findings |
| `rows[].hallucination_placeholder` | `not_scored` without human labels |
| `rows[].error_placeholder` | live errors only when keys present |
| `reproducibility.rows_sha256` | hash of sorted rows |

## Commands

```text
cd backend
.venv\Scripts\python.exe -m aerobim.tools.benchmark_llm_advisory
```

Live Yandex remarks bake-off remains a **separate** opt-in tool (`run_yandex_remarks_bakeoff`) — not wired into production analyze.

## Forbidden claims

Do not treat mock agreement, latency, or schema_valid rates as customer precision, >90%, or production readiness.
