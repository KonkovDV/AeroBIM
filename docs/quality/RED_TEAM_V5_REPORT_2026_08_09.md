# Red Team v5 — промежуточный отчёт (2026-08-09)

## 1. Точка отсчёта

| Поле | Значение | Команда |
|---|---|---|
| base main | `5a75d866cce256d8b4caa010031683762b8ee162` | `git rev-parse origin/main` |
| tree | `0401bdd209f1ad18dd18d6b8949d96716f9efd6f` | `git rev-parse HEAD^{tree}` (на main) |
| ветка работ | `red-team/v5-p0-closure` | |
| `gh auth` | KonkovDV OK | `gh auth status` |
| open PR (на старте) | `[]` | `gh pr list` |
| merge CI | [31301092314](https://github.com/KonkovDV/AeroBIM/actions/runs/31301092314) success | |
| CI artifact (PR #12) | [31300803466](https://github.com/KonkovDV/AeroBIM/actions/runs/31300803466) / run `31301092306` | download `ci-runtime-baseline` |

`git status --porcelain` в начале аудита: чисто. После работ — см. PR.

## 2. Гиперглубокий аудит

→ [`docs/audit/REPO_DEEP_MAP_2026_08_09.md`](../audit/REPO_DEEP_MAP_2026_08_09.md)

Новые находки **N-32…N-38** внутри карты.

## 3. Реестр N-1…N-31

→ [`docs/quality/FINDINGS_N1_N31_RESYNC_2026_08_09.md`](FINDINGS_N1_N31_RESYNC_2026_08_09.md)

## 4. Пакеты P0 / K (этот PR)

| Пакет | Статус | Что |
|---|---|---|
| WP-N30 circular | FIXED ранее | `#12` |
| WP-A1b generation | **в этом PR** | CI больше не `--run-gates`; junit+vitest+PASS gates; refuse non-publishable generate |
| WP-A12 | partial | baseline cleaned; `audit/evidence/**` ещё N-34 |
| WP-N25/26 | FIXED ранее | |
| WP-N27/28 | **в этом PR** | metadata + table boundary |
| WP-N29 | **FIXED_BY_US** | allow-file требует registry path; A8 KILLED |
| WP-A11 | pending | после зелёного CI — commit artifact |
| WP-G4 | **обновлён** | PR_TRIAGE |
| K1 | **в этом PR** | `docs/docs.md` §7 |
| K2 | **черновик** | `deployment-contour-2026.md` |
| K3 | **черновик** | `ACCEPTANCE_PROTOCOL_TASK7_2026.md` |
| K4–K11 | K4 partial | CoverageMapPanel 12 tests + DrawingEvidencePanel 12 tests |

## 5. Самоатаки

→ [`RED_TEAM_SELFATTACK_2026_08_09.md`](RED_TEAM_SELFATTACK_2026_08_09.md) — 14 KILLED / 0 SURVIVED / 6 UNVERIFIED.

## 6. Итоговый baseline

Пока committed: `publishable: false`, `attested_by: local`.  
Цель после зелёного CI этой ветки + follow-up PR: `publishable: true`, `attested_by: ci`, непустой `run_id`, `gates_attested` ×7, `artifact_completeness: full`.

## 7. Расхождения с промтом

См. карту §0 (SHA, ветки, PR, пути, schema).  
`attested_by` в коде = `"ci"`, не `"github-actions"` (промт §4) — SSOT кода сохранён.

## 8. Оценка готовности (предварительно)

| | % | Блокер |
|---|---:|---|
| ТЗ | ≈35 | RT-001/002/003, DWG, corpus |
| КТ#2 | ≈78–82 | WP-A1b publishable artifact на main; frontend tests; self-attacks ≥14 |

**DoD п.1 ещё не закрыт** до commit CI-attested baseline.
