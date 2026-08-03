---
title: "Red Team — live AECV-Bench on Yandex Qwen (open-bench only)"
status: active
version: "1.0.0"
last_updated: "2026-08-04"
claim_boundary: >-
  Public-floor-plan object-counting baseline only. Not AeroBIM product accuracy.
  closes_rt001=false. Checkpoint remains NO_GO. RT-001/002/003 open.
---

# Red Team note — AECV live counting (2026-08-04)

## What was run

| Field | Value |
|---|---|
| Harness | AECV-Bench Use Case 1 object counting (120 plans) |
| Provider | Yandex AI Studio |
| Model | `qwen3.6-35b-a3b` (`gpt://b1g56rei64gfdk5t2tvc/qwen3.6-35b-a3b`) |
| Tool | `python -m aerobim.tools.run_aecv_bench_eval --mode live --limit 120` |
| Thinking | `chat_template_kwargs.enable_thinking=false` (top-level `enable_thinking` → HTTP 400) |
| Product LLM | `AEROBIM_LLM_LOCAL_ENABLED=false` (advisory path still opt-in) |

## Numbers (exact-match rate)

| Scope | Result |
|---|---|
| Attempted / scored / errors | **120 / 117 / 3** |
| Macro exact-match | **0.4325** |
| Door | 0.2308 |
| Window | 0.1368 |
| Space | 0.1368 |
| Bedroom | 0.8462 |
| Toilet | 0.8120 |

Errors: plans `2000-0008`, `2000-0009`, `2000-0012` (tiny `.jpg` ≈10 KB → vendor HTTP 400).

## Red Team reading

1. **Matches literature gradient:** room-type fields strong; symbol counting (Door/Window/Space) weak — do not sell «vision works» as «counts symbols».
2. **Not RT-001:** public plans ≠ Samolet dual-expert TP/FP. `claim_level=open_bench_only`.
3. **Not Checkpoint GO:** customer blockers unchanged.
4. **Not product path proof:** live bench used Studio credentials from gitignored `.env`; product analyze overlay remains disabled until operator enable + budget ledger.

## Evidence

- [`../evidence/aecv-bench-eval-latest.json`](../evidence/aecv-bench-eval-latest.json)
- Decision levels: [`OPEN_BENCH_VS_RT001_DECISION_2026_08_04.md`](OPEN_BENCH_VS_RT001_DECISION_2026_08_04.md)
- Prior claims audit: [`RED_TEAM_WORLD_PRACTICES_A1_A8_2026_08_04.md`](RED_TEAM_WORLD_PRACTICES_A1_A8_2026_08_04.md)

## Forbidden slides

- «Точность AeroBIM 43%» / «>90%»
- «Мультимодальность подтверждена для пилота»
- «RT-001 закрыт open-bench’ем»
