---
title: "Yandex AI Studio grant ops — stage report"
date: 2026-08-03
status: ready_for_budget_then_enable
version: "1.8.0"
claim_boundary: "Not Checkpoint GO. Open-bench AECV counting measured (macro 0.4325) ≠ product accuracy. Thinking off via chat_template_kwargs only. Run cap 100k. Never paste API key."
ids: "folder b1g56rei64gfdk5t2tvc; kill-switch ajeomh7lns01j2lv3dcc"
---

# Grant ops v1.8 — open-bench live + thinking pin

## Limits (post-measure)

| Cap | Value | Why |
|---|---|---|
| `MAX_TOKENS_PER_RUN` | **100 000** | Measured ~44k/100 findings; old 250k ≈ 5 packs before trip |
| `MAX_TOKENS_PER_DAY` | **300 000** | Card-bound; no TRIAL_EXPIRED |
| Per remark | **~440 tok** (254p+186c, think off) | Real FireRating finding |

₽/pack = 44k × console tariff for `qwen3.6-35b-a3b` (still open).

## Mandatory: thinking off via `chat_template_kwargs`

Not a perf tweak. Without it, `json_schema` → empty `content`, reasoning burns `max_tokens`.

| Placement | Vendor result |
|---|---|
| `chat_template_kwargs.enable_thinking=false` | **OK** (content returned) |
| Top-level `enable_thinking` / `extra_body` | **HTTP 400** Unsupported parameter |

Open-bench tool `run_aecv_bench_eval` and product adapter must use the kwargs form. **Do not** reintroduce top-level flags.

## Seed / P₁

`seed` returns HTTP 200 but MoE shared-instance determinism is unproven. Keep `send_seed=false`. Optional pre-KT#2: P₁ (5 identical calls, hash compare) ≈ 2k tokens / ~1 ₽.

## Vision claim hygiene

| Claim | Status |
|---|---|
| Endpoint accepts images | Verified |
| Open-bench AECV counting (Yandex Qwen) | **Measured** 2026-08-04 — macro exact-match **0.4325**; Door/Window/Space weak | 
| Product / pilot multimodal accuracy | **NOT claimed** (`open_bench_only`; Checkpoint **NO_GO**) |

Incorrect: «мультимодальность подтверждена для Самолёта».

Evidence: `docs/evidence/aecv-bench-eval-latest.json` · Red Team: `docs/quality/RED_TEAM_AECV_LIVE_YANDEX_2026_08_04.md`.

## G1

Wired (`overlay_llm_remarks`). OFF==ON on UC path is non-vacuous once `LOCAL_ENABLED=true`.

## Red Team audit

| Area | Verdict |
|---|---|
| Secrets in code/logs | Pass (key only in gitignored `.env`) |
| ADR-001 / `summary.passed` | Pass |
| Thinking-off placement | Pass (`chat_template_kwargs`) |
| Host allowlist / SSRF | Pass |
| `/latest` in config | Pass (forbidden); vendor echo recorded |
| L1 sold as L3 | **Forbidden** — enforced in Claims Lock wording |

Residual: console/curl spend bypasses AeroBIM; kill-switch = revoke `ajeomh7lns01j2lv3dcc`.

## Operator order

1. Console tariff → 44k → ₽  
2. Budget 6 000 ₽/мес + kill-switch id beside 85% alert  
3. `AEROBIM_LLM_LOCAL_ENABLED=true` (product path — separate from open-bench CLI)  
4. Fixture pack: record actual ₽; assert `passed` / `error_count` / `warning_count` match OFF run
