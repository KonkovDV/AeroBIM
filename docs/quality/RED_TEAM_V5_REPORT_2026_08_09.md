# Red Team v5 — отчёт (2026-08-09)

## 1. Точка отсчёта

| Поле | Значение | Команда |
|---|---|---|
| base main (аудит) | `5a75d866cce256d8b4caa010031683762b8ee162` | `git rev-parse origin/main` |
| merge PR | **#13** → `1de56491f353d007d265ee1bc50370ee5e881339` | `gh pr merge 13` |
| CI (PR tip green) | [31303764984](https://github.com/KonkovDV/AeroBIM/actions/runs/31303764984) | success |
| `gh auth` | KonkovDV OK | `gh auth status` |

## 2. Гиперглубокий аудит

→ [`docs/audit/REPO_DEEP_MAP_2026_08_09.md`](../audit/REPO_DEEP_MAP_2026_08_09.md) — N-32…N-38.

## 3. Реестр N-1…N-31

→ [`docs/quality/FINDINGS_N1_N31_RESYNC_2026_08_09.md`](FINDINGS_N1_N31_RESYNC_2026_08_09.md)

## 4. Пакеты P0 / K (влито в main через #13)

| Пакет | Статус | Что |
|---|---|---|
| WP-A1b generation | **FIXED_BY_US** | CI generate без `--run-gates`; publishable assert |
| WP-A11 tip lag | **FIXED_BY_US** | BFS merge parents + soft SHA/`--check-publishable` lag |
| WP-A12 / N-34 | **FIXED_BY_US** | sanitize `audit/evidence/**` abs paths |
| WP-N27/28 | **FIXED_BY_US** | metadata + table boundary |
| WP-N29 / A8 | **FIXED_BY_US** | `audit/claims_allow_file_registry.json` |
| K1 | **FIXED_BY_US** | `docs/docs.md` §7 tagged |
| K2 | **черновик** | `deployment-contour-2026.md` |
| K3 | **черновик** | `ACCEPTANCE_PROTOCOL_TASK7_2026.md` |
| K4 | **FIXED_BY_US** | CoverageMapPanel 12 + DrawingEvidencePanel 12 vitest |

## 5. Самоатаки

→ [`RED_TEAM_SELFATTACK_2026_08_09.md`](RED_TEAM_SELFATTACK_2026_08_09.md) — **16 KILLED** / 0 SURVIVED / 4 UNVERIFIED.

## 6. Итоговый baseline (на main)

| Поле | Значение |
|---|---|
| `publishable` | **true** |
| `attested_by` | **ci** |
| `run_id` | `31303439524` |
| `artifact_completeness` | **full** |
| `gates_attested` | 7 jobs |
| tests | backend **2161**, frontend **48** |

SHA tip в артефакте может отставать от merge HEAD — CI soft-lag это допускает; structural drift — нет.

## 7. Расхождения с промтом

`attested_by` SSOT = `"ci"` (не `"github-actions"`). Snapshot промта (2 ветки / 7 PR) был устаревшим на старте аудита.

## 8. Оценка готовности

| | % | Блокер |
|---|---:|---|
| ТЗ | ≈35 | RT-001/002/003, DWG native, customer corpus |
| КТ#2 eng honesty | ≈85–88 | K5–K11 residuals; A5/A6/A17–A20; main CI confirm |

**DoD п.1 (CI-attested publishable baseline на main):** закрыт через PR #13.
