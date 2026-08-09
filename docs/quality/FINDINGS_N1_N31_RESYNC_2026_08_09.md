# Реестр находок N-1…N-31 — пересверка 2026-08-09 (v5)

**Дерево:** `git rev-parse HEAD` → см. текущую ветку `red-team/v5-p0-closure` (база `5a75d86`).  
**Словарь статусов:** только STILL_TRUE / FIXED_BY_US / WAS_FALSE / SUPERSEDED / ASSUMED / UNVERIFIED.

| № | Статус | Доказательство | Коммит-фикс |
|---|---|---|---|
| N-1 | **STILL_TRUE** | committed baseline `attested_by: local`, `run_id: null` | — (ждёт WP-A1b commit CI artifact) |
| N-2 | **STILL_TRUE** | то же; структурная самоаттестация закрыта кодом N-18, но артефакт ещё local | частично `76e0da0` |
| N-4 | **STILL_TRUE** | frontend vitest 29 vs backend collected 2006 | — WP-B3 |
| N-6 | **FIXED_BY_US** | ENGINEERING_STATUS frontmatter/body v1.6.6 | до `af6e364` |
| N-10 | **STILL_TRUE** | Exp B coverage-map ≠ >90%; не «чинить» цифру | — K4 |
| N-11 | **ASSUMED** | ГОСТ 21.101-2026 ссылки не прогнаны в этом прогоне | — |
| N-12 | **STILL_TRUE** (by design) | native DWG fail-closed; не реализовывать | — |
| N-14 | **ASSUMED** | README regen без ручной правки — скрипт есть; тест «запрет ручной» UNVERIFIED | — |
| N-15 | **ASSUMED** | LIC-001 Option B — полная перечитка не в этом прогоне | — |
| N-17 | **ASSUMED** | benchmark advisory+enforced — не перепроверено командой | — |
| N-18 | **FIXED_BY_US** | attestation только из GITHUB_* | `bf12874`… |
| N-19 | **FIXED_BY_US** | ruff/mypy PASS в baseline gates | `e709463`… |
| N-20 | **FIXED_BY_US** | documented⊇code в baseline algo; сырой regex даёт N-33 | `bf12874` |
| N-22 | **FIXED_BY_US** | `--check-publishable` в CI рядом с compare | `bf12874` |
| N-23 | **FIXED_BY_US** (код) / **STILL_TRUE** (артефакт) | `gates_attested` пуст в committed; в CI env работает | `bf12874` |
| N-24 | **FIXED_BY_US** (committed baseline) / **STILL_TRUE** (`audit/evidence/**`) | санитайзер + тест; N-34 | `76e0da0`+ |
| N-25 | **FIXED_BY_US** | `--check-publishable` → error если не publishable | `76e0da0` |
| N-26 | **FIXED_BY_US** | refuse local write committed path exit 2 | `76e0da0` |
| N-27 | **FIXED_BY_US** (этот PR) | мёртвый `pass` убран; `_MONITORED` расширен; fail-closed git date | эта ветка |
| N-28 | **FIXED_BY_US** (этот PR) | table rows checked; тест | эта ветка |
| N-29 | **FIXED_BY_US** (этот PR) | allow-file не амнистия; тест | эта ветка |
| N-30 | **FIXED_BY_US** (circular) / **STILL_TRUE** (residual) | circular lock снят (`:883`); CI `--run-gates` ломал publishable — чинится в этом PR | `76e0da0` + эта ветка |
| N-31 | **SUPERSEDED** | open PR=0; политика через PR; triage обновлён | #12 + эта ветка |
| N-32…N-38 | см. `REPO_DEEP_MAP_2026_08_09.md` | новые | — |

**WAS_FALSE:** в этом прогоне **не** выставлялся (нет worktree на исходный SHA промта `498fd709`).
