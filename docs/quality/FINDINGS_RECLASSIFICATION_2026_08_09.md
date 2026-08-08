# Findings reclassification — 2026-08-09 (v4 / Step 0-bis)

Словарь: `WAS_FALSE` | `SUPERSEDED` | `FIXED_BY_US` | `STILL_TRUE` | `ASSUMED` | `UNVERIFIED`.

См. также: [`audit/reports/CRITICAL_BLOCKERS.md`](../../audit/reports/CRITICAL_BLOCKERS.md) (N-18).

| # | Утверждение (Step 0) | Статус | Доказательство |
|---|----------------------|--------|----------------|
| 1 | `schema_version` 1.3.0 | **SUPERSEDED** | `main` @ `8ef9f9b`: `docs/evidence/runtime-baseline-latest.json` → `1.3.0`; ветка → `1.4.0` после WP-A1 |
| 2 | `commit_sha` / `tree_sha` | **SUPERSEDED** | `main` → `8ef9f9b` / `cddafd8f`; ветка ушла вперёд локально |
| 3 | `working_tree_clean: true` | **SUPERSEDED** | `main` true; ветка dirty до коммита |
| 4 | `publishable: true` | **SUPERSEDED** | `main` true (Windows attestation); ветка → `false` до CI artifact (WP-A11) |
| 5 | backend 1988 / 1980 | **SUPERSEDED** | `main` baseline; ветка → 1997/1990 после правок |
| 6 | разрыв `test_functions` 1990 vs 1988 | **FIXED_BY_US** | `test_edge_cases.py`, `test_layer_boundaries.py`; baseline `uncollected: []` |
| 7 | lockfile не менялся | **FIXED_BY_US** | `python-docx==1.2.0`, `openpyxl==3.1.5` в `requirements-lock.txt`; sha `c70becc6…` |
| 8 | `docs/**` не в claims-lint | **FIXED_BY_US** | `--full-docs` в CI `.github/workflows/ci.yml` (ветка) |
| 9 | амнистия `_line_is_documented_forbidden_context` | **FIXED_BY_US** | функция удалена; `allow-file` / `allow reason` |
| 10 | обход `matrix_guard` для MEP | **FIXED_BY_US** | `audit/tz_matrix_blocked_registry.json` + тест `test_matrix_guard_catches_mep_row_marked_done` |
| 11 | README «171 tests / 1.9K LOC» | **WAS_FALSE** | `rg` на `main` и ветке: совпадений нет (кэш-гипотеза подтверждена как ложная) |
| 12 | `AEROBIM_REMARK_LOCALE` / `PRIORITY_PROFILE` | **FIXED_BY_US** | `_check_code_env_documented`; `comm` код↔baseline пуст на ветке |
| 13 | дрейф ENGINEERING_STATUS | **FIXED_BY_US** | WP-A3: v1.6.6, Schema 1.4.0, 48/72/63 |
| 14 | пропуск пункта 8 Non-claims | **FIXED_BY_US** | `pilot-claim-boundary-2026.md` п.8 (Experiment B) |
| 15 | frontend 29 тестов | **STILL_TRUE** | `vitest-results.json` → 29; соотношение ~1:69 |
| 16 | 5 quality_gates PASS | **ASSUMED** | локально ruff/mypy FAIL без `--run-gates`; CI — источник истины |
| 17 | 7 открытых PR | **UNVERIFIED** | `gh pr list` → HTTP 401 (09.08) |
| 18 | CoverageMapPanel без теста | **STILL_TRUE** | компонент есть; `*.test.*` для панели нет (WP-B3) |

**N-18 (новое):** `attested_by` из CLI `--attested-by` → **FIXED_BY_US** (WP-A1b): флаг удалён; аттестация только из `GITHUB_ACTIONS` + `GITHUB_RUN_ID` + `GITHUB_WORKFLOW_REF` + `GITHUB_SHA`.
