# Реестр находок N-1…N-31 — пересверка 2026-08-09 (v5) + post-merge

**Дерево:** `main` @ merge #13/#14.  
**Словарь статусов:** только STILL_TRUE / FIXED_BY_US / WAS_FALSE / SUPERSEDED / ASSUMED / UNVERIFIED.

| № | Статус | Доказательство | Коммит-фикс |
|---|---|---|---|
| N-1 | **FIXED_BY_US** | committed baseline `attested_by: ci`, non-null `run_id`, `publishable: true` | #13 / #14 |
| N-2 | **FIXED_BY_US** | artifact CI-attested; structural self-check + publishable | #13 |
| N-4 | **FIXED_BY_US** | frontend vitest **48** (CoverageMap+DrawingEvidence ≥12 each) | #13 |
| N-6 | **FIXED_BY_US** | ENGINEERING_STATUS frontmatter/body v1.6.6 | до `af6e364` |
| N-10 | **STILL_TRUE** | Exp B coverage-map ≠ product >90%; не «чинить» цифру | honesty / K4 |
| N-11 | **ASSUMED** | ГОСТ 21.101-2026 ссылки не прогнаны в этом прогоне | — |
| N-12 | **STILL_TRUE** (by design) | native DWG fail-closed; не реализовывать | — |
| N-14 | **FIXED_BY_US** | A6: forged README snippet fails `_check_readme_markers` | #14 |
| N-15 | **ASSUMED** | LIC-001 Option B — полная перечитка не в этом прогоне | — |
| N-17 | **ASSUMED** | benchmark advisory+enforced — не перепроверено командой | — |
| N-18 | **FIXED_BY_US** | attestation только из GITHUB_* | `bf12874`… |
| N-19 | **FIXED_BY_US** | ruff/mypy PASS в baseline gates | `e709463`… |
| N-20 | **FIXED_BY_US** | documented⊇code в baseline algo; сырой regex даёт N-33 | `bf12874` |
| N-22 | **FIXED_BY_US** | `--check-publishable` в CI рядом с compare | `bf12874` |
| N-23 | **FIXED_BY_US** | committed `gates_attested` ×7 из CI artifact | #13/#14 |
| N-24 | **FIXED_BY_US** | committed baseline + `audit/evidence/**` abs paths sanitized | #13 + hygiene |
| N-25 | **FIXED_BY_US** | `--check-publishable` → error если не publishable | `76e0da0` |
| N-26 | **FIXED_BY_US** | refuse local write committed path exit 2 | `76e0da0` |
| N-27 | **FIXED_BY_US** | мёртвый `pass` убран; `_MONITORED` расширен; fail-closed git date | #13 |
| N-28 | **FIXED_BY_US** | table rows checked; тест | #13 |
| N-29 | **FIXED_BY_US** | allow-file только через registry; A8 KILLED | #13 |
| N-30 | **FIXED_BY_US** | circular lock снят; CI generate без `--run-gates` | #12 + #13 |
| N-31 | **SUPERSEDED** | политика: один `main`, PR → merge → delete branch | #12–#14 |
| N-32…N-38 | см. `REPO_DEEP_MAP_2026_08_09.md` | N-34/36 closed on main; N-33/35/37/38 tracking | — |

**WAS_FALSE:** в этом прогоне **не** выставлялся (нет worktree на исходный SHA промта `498fd709`).
