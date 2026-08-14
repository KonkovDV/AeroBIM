<!-- claims-lint: allow-file reason="N43 monitoring only; do not activate before 17.08" -->
---
title: "N43 baseline SHA — мониторинг 14.08.2026"
date: "2026-08-14"
claim_boundary: "Soft window check. Does not flip N43. Does not regenerate runtime baseline."
---

# N43 monitoring (пункт 17.2, срез 14.08)

Политика до 17.08: `max_commits_behind=50`, waiver `N43-baseline-one-commit-lag` = **deferred**.  
Чеклист активации: [`N43_REHEARSAL_CHECKLIST_2026_08_17.md`](N43_REHEARSAL_CHECKLIST_2026_08_17.md).

| Поле | Значение |
| --- | --- |
| Artifact commit | `3489cad44697c4378eebca8bc5552c7a853f2749` (`docs/evidence/runtime-baseline-latest.json`) |
| HEAD на замере | `aca6d09` |
| `git rev-list --count 3489cad..HEAD` | **62** |
| Порог `when_deferred` | 50 |
| Soft window | **превышен** (62 > 50) |
| Активация lag=1 | **не делать** до 17.08 |

CI `--check-committed-baseline` на tip-lag может уходить в SOFT skip (см. `.github/workflows/ci.yml`). Это не зелёный N43.

**17.08 обязательно:** экспорт нового `runtime-baseline-latest.json` на tip **до** `max_commits_behind=1`. Иначе активация сразу красная.
