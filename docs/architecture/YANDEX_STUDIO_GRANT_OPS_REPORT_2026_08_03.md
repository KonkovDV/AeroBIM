---
title: "Yandex AI Studio grant ops — stage report"
date: 2026-08-03
status: ready_for_budget_then_enable
version: "1.7.0"
claim_boundary: "Not Checkpoint GO. Vision = endpoint accepts images; recognition NOT_MEASURED. enable_thinking=false is mandatory for 5.1. Run cap 100k. Never paste API key."
ids: "folder b1g56rei64gfdk5t2tvc; kill-switch ajeomh7lns01j2lv3dcc"
---

# Grant ops v1.7 — fuse tightened

## Limits (post-measure)

| Cap | Value | Why |
|---|---|---|
| `MAX_TOKENS_PER_RUN` | **100 000** | Measured ~44k/100 findings; old 250k ≈ 5 packs before trip |
| `MAX_TOKENS_PER_DAY` | **300 000** | Card-bound; no TRIAL_EXPIRED |
| Per remark | **~440 tok** (254p+186c, think off) | Real FireRating finding |

₽/pack = 44k × console tariff for `qwen3.6-35b-a3b` (still open).

## Mandatory: `enable_thinking=false`

Not a perf tweak. Without it, `json_schema` → empty `content`, reasoning burns `max_tokens`. Documented in adapter comments + this report. **Do not remove.**

## Seed / P₁

`seed` returns HTTP 200 but MoE shared-instance determinism is unproven. Keep `send_seed=false`. Optional pre-KT#2: P₁ (5 identical calls, hash compare) ≈ 2k tokens / ~1 ₽.

## Vision claim hygiene

Correct: «эндпоинт принимает изображения; качество распознавания **NOT_MEASURED**».  
Incorrect: «мультимодальность подтверждена».

## G1

Wired (`overlay_llm_remarks`). OFF==ON on UC path is non-vacuous once `LOCAL_ENABLED=true`.

## Red Team audit (2026-08-03, uncommitted → this commit)

| Severity | Location | Finding |
|---|---|---|
| Medium | `settings.py` / `bootstrap._build_llm_advisory_provider` | `AEROBIM_LLM_BUDGET_LEDGER` documented as required for grant ops but **not fail-closed at boot** → N workers ≈ N× day cap on card-bound account |
| Medium | `advisory_remark_overlay.py` | Analyze overlay calls Studio **without** `HybridRouteGate` / CLI hybrid audit parity |

| Area | Verdict |
|---|---|
| Secrets in code/logs | Pass |
| ADR-001 / `summary.passed` | Pass |
| `enable_thinking=false` | Pass (mandatory for 5.1) |
| Host allowlist / SSRF | Pass |
| Stamp/PII gate | Not weakened |
| `/latest` in config | Pass (forbidden); vendor echo recorded |
| Critical / High | **None** |

Residual: console/curl spend bypasses AeroBIM; kill-switch = revoke `ajeomh7lns01j2lv3dcc`.

## Operator order (unchanged)

1. Console tariff → 44k → ₽  
2. Budget 6 000 ₽/мес + kill-switch id beside 85% alert  
3. `AEROBIM_LLM_LOCAL_ENABLED=true`  
4. Fixture pack: record actual ₽; assert `passed` / `error_count` / `warning_count` match OFF run
